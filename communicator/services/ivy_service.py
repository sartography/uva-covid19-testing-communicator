import csv
from datetime import datetime

import globus_sdk
from dateutil import parser

from communicator import app, db
from communicator.errors import CommError
from communicator.models.ivy_file import IvyFile
from communicator.models.sample import Sample
from os import listdir
from os.path import isfile, join


class IvyService(object):
    """Opens files uploaded to the server from IVY and imports them into the database. """

    def __init__(self):
        self.path = app.config['IVY_IMPORT_DIR']
        self.GLOBUS_CLIENT_ID = app.config['GLOBUS_CLIENT_ID']
        self.GLOBUS_TRANSFER_RT = app.config['GLOBUS_TRANSFER_RT']
        self.GLOBUS_TRANSFER_AT = app.config['GLOBUS_TRANSFER_AT']
        self.EXPIRES_AT = 1600601877
        self.GLOBUS_IVY_ENDPOINT = app.config['GLOBUS_IVY_ENDPOINT']
        self.GLOBUS_DTN_ENDPOINT = app.config['GLOBUS_DTN_ENDPOINT']
        self.GLOBUS_IVY_PATH = app.config['GLOBUS_IVY_PATH']
        self.GLOBUS_DTN_PATH = app.config['GLOBUS_DTN_PATH']


    def load_directory(self, delete_from_globus=True):
        onlyfiles = [f for f in listdir(self.path) if isfile(join(self.path, f))]
        app.logger.info(f'Loading directory {self.path}')

        samples = []
        for file_name in onlyfiles:
            samples = IvyService.samples_from_ivy_file(join(self.path, file_name))
            ivy_file = db.session.query(IvyFile).filter(IvyFile.file_name == file_name).first()
            if not ivy_file:
                ivy_file = IvyFile(file_name=file_name, sample_count=len(samples))
            else:
                ivy_file.date_added = datetime.now()
                ivy_file.sample_count = len(samples)
            db.session.add(ivy_file)
            db.session.commit()
            app.logger.info(f'Loading file {file_name}')
            if(delete_from_globus):
                self.delete_file(file_name)
        return samples

    @staticmethod
    def samples_from_ivy_file(file_name):
        rows = []
        with open(file_name, 'r') as csv_file:
            reader = csv.DictReader(csv_file, delimiter='|')
            for row in reader:
                sample = IvyService.record_to_sample(row)
                rows.append(sample)
        return rows

    @staticmethod
    def record_to_sample(dictionary):
        """Creates a Test Result from a record read in from the IVY CSV File"""
        sample = Sample()
        try:
            sample.barcode = f"{dictionary['Student ID']}-{dictionary['Test Date Time']}-{dictionary['Test Kiosk Loc']}"
            sample.student_id = dictionary["Student ID"]
            sample.phone = dictionary["Student Cellphone"]
            sample.email = dictionary["Student Email"]
            sample.date = parser.parse(dictionary["Test Date Time"])
            sample.location = dictionary["Test Kiosk Loc"]
            sample.result_code = dictionary["Test Result Code"]
            sample.in_ivy = True
            return sample
        except KeyError as e:
            raise CommError("100", f"Invalid CSV Record, missing column {e}")


    def get_access_token(self):

        client = globus_sdk.NativeAppAuthClient(self.GLOBUS_CLIENT_ID)
        client.oauth2_start_flow(refresh_tokens=True)

        authorize_url = client.oauth2_get_authorize_url()
        print('Please go to this URL and login: {0}'.format(authorize_url))

        # this is to work on Python2 and Python3 -- you can just use raw_input() or
        # input() for your specific version
        get_input = getattr(__builtins__, 'raw_input', input)
        auth_code = get_input(
            'Please enter the code you get after login here: ').strip()
        token_response = client.oauth2_exchange_code_for_tokens(auth_code)

        globus_auth_data = token_response.by_resource_server['auth.globus.org']

        # let's get stuff for the Globus Transfer service
        globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']
        # the refresh token and access token, often abbr. as RT and AT
        transfer_rt = globus_transfer_data['refresh_token']
        transfer_at = globus_transfer_data['access_token']
        expires_at_s = globus_transfer_data['expires_at_seconds']

        # Now we've got the data we need, but what do we do?
        # That "GlobusAuthorizer" from before is about to come to the rescue

        authorizer = globus_sdk.RefreshTokenAuthorizer(
            transfer_rt, client, access_token=transfer_at)

        # and try using `tc` to make TransferClient calls. Everything should just
        # work -- for days and days, months and months, even years
        tc = globus_sdk.TransferClient(authorizer=authorizer)

        print("The Transfer Token is:" + transfer_rt)
        print("The Access Token: " + transfer_at)
        print("Expires At: " + str(expires_at_s))


    def get_transfer_client(self):
        self.client = globus_sdk.NativeAppAuthClient(self.GLOBUS_CLIENT_ID)
        self.client.oauth2_start_flow(refresh_tokens=True)

        authorizer = globus_sdk.RefreshTokenAuthorizer(
            self.GLOBUS_TRANSFER_RT, self.client, access_token=self.GLOBUS_TRANSFER_AT, expires_at=self.EXPIRES_AT)
        tc = globus_sdk.TransferClient(authorizer=authorizer)

        r = tc.endpoint_autoactivate(self.GLOBUS_IVY_ENDPOINT, if_expires_in=3600)
        r = tc.endpoint_autoactivate(self.GLOBUS_DTN_ENDPOINT, if_expires_in=3600)
        print(str(r))
        if r['code'] == 'AutoActivationFailed':
            print('Endpoint({}) Not Active! Error! Source message: {}'.format(self.GLOBUS_CLIENT_ID, r['message']))
        elif r['code'] == 'AutoActivated.CachedCredential':
            print('Endpoint({}) autoactivated using a cached credential.'.format(self.GLOBUS_CLIENT_ID))
        elif r['code'] == 'AutoActivated.GlobusOnlineCredential':
            print(('Endpoint({}) autoactivated using a built-in Globus credential.').format(self.GLOBUS_CLIENT_ID))
        elif r['code'] == 'AlreadyActivated':
            print('Endpoint({}) already active until at least {}'.format(self.GLOBUS_CLIENT_ID, 3600))
        return tc

    def request_transfer(self):
        tc = self.get_transfer_client()
        tdata = globus_sdk.TransferData(tc, self.GLOBUS_IVY_ENDPOINT, self.GLOBUS_DTN_ENDPOINT, label="Transfer",
                                        sync_level="checksum")
        tdata.add_item(self.GLOBUS_IVY_PATH, self.GLOBUS_DTN_PATH, recursive = True)
        transfer_result = tc.submit_transfer(tdata)
        print("Trasfer requested:" + str(transfer_result))

    def list_files(self):
        tc = self.get_transfer_client()
        response = tc.operation_ls(self.GLOBUS_DTN_ENDPOINT, path="/~/project/covid-vpr")
#        response = tc.my_shared_endpoint_list(self.GLOBUS_DTN_ENDPOINT)
        print("What is there?")
        print(response)

    def delete_file(self, file_name):
        tc = self.get_transfer_client()
        ddata = globus_sdk.DeleteData(tc, self.GLOBUS_DTN_ENDPOINT, recursive=True)
        file_path = f"{self.GLOBUS_DTN_PATH}/{file_name}"
        ddata.add_item(file_path)
        delete_result = tc.submit_delete(ddata)
        app.logger.info("Requested deleting file: " + file_path)
        app.logger.info("Deleted Covid-vpr file:" + str(delete_result))

        ddata = globus_sdk.DeleteData(tc, self.GLOBUS_IVY_ENDPOINT, recursive=True)
        file_path = f"{self.GLOBUS_IVY_PATH}/{file_name}"
        ddata.add_item(file_path)
        delete_result = tc.submit_delete(ddata)
        app.logger.info("Requested deleting file: " + file_path)
        app.logger.info("Deleted ics file:" + str(delete_result))

