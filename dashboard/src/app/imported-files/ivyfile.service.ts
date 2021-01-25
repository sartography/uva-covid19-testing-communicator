import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';

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
  getFiles(): Observable<IvyFile[]> {
    return this.http
      .get<IvyFile[]>(`http://0.0.0.0:5000/v1.0/ivy_file`).pipe(
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