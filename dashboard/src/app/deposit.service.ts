import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';

import { Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { HttpHeaders } from '@angular/common/http';

const httpOptions = {
  headers: new HttpHeaders({
    'Content-Type':  'application/json',
    Authorization: 'my-auth-token'
  })
};

// import {API_URL} from '../env';

import {Deposit} from './deposit'

@Injectable()
export class DepositService {

  constructor(private http: HttpClient) {
  }

  // GET list of public, future events
  getDeposits(): Observable<Deposit[]> {
    return this.http
      .get<Deposit[]>(`http://0.0.0.0:5000/get_inventory_deposits`).pipe(
        tap(_ => this.log('fetched files')),
        catchError(this.handleError<Deposit[]>('getDeposits', []))
      );
  }

    /** POST: add a new hero to the database */
    addDeposit(deposit: Deposit): Observable<Deposit> {
      return this.http.post<Deposit>(`http://0.0.0.0:5000/add_inventory_deposit`, deposit, httpOptions)
        .pipe(
          catchError(this.handleError('addDeposit', deposit))
        );
    }
    /**
   * Handle Http operation that failed.
   * Let the app continue.
   * @param operation - name of the operation that failed
   * @param result - optional value to return as the observable result
   */
  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {

      // TODO: send the error to remote logging infrastructure
      console.error(error); // log to console instead

      // TODO: better job of transforming error for user consumption
      this.log(`${operation} failed: ${error.message}`);

      // Let the app keep running by returning an empty result.
      return of(result as T);
    };
  }

  /** Log a HeroService message with the MessageService */
  private log(message: string) {
    console.log(message);
    //this.messageService.add(`HeroService: ${message}`);
  }
}