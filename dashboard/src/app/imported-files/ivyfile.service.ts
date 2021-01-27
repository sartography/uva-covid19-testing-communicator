import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse, HttpParams} from '@angular/common/http';

import { Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';


// import {API_URL} from '../env';

import {IvyFile} from './ivyfile'

@Injectable()
export class IvyFileService {

  constructor(private http: HttpClient) {
  }

  // GET list of public, future events
  getFiles(page: Number): Observable<IvyFile[]> {
    let params = new HttpParams().set("page",String(page));
    return this.http
      .get<IvyFile[]>(`${environment.api_url}/ivy_file`,{params: params}).pipe(
        tap(_ => this.log('fetched files')),
        catchError(this.handleError<IvyFile[]>('getFiles', []))
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