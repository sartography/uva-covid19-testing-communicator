import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';

import { Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { HttpParams } from '@angular/common/http';

import { environment } from '../../environments/environment';

import { Sample } from '../sample';
import { SearchForm } from '../search_form';

@Injectable()
export class GraphService {

  constructor(private http: HttpClient) {
  }
  getDayData(form: SearchForm): Observable<JSON> {
    let params = new HttpParams()
      .set("start_date", form.start_date)
      .set("end_date", form.end_date)
      .set("student_id", form.student_id)
      .set("compute_id", form.compute_id)
      .set("location", form.location)
    return this.http
      .get<JSON>(`${environment.api_url}/graphs/day`, { params: params }).pipe(
        tap(_ => this.log('building day graph')),
        catchError(this.handleError<JSON>('getDayData', <JSON>{}))
      );
  }
  
  getWeekdayData(form: SearchForm): Observable<JSON> {
    let params = new HttpParams()
      .set("start_date", form.start_date)
      .set("end_date", form.end_date)
      .set("student_id", form.student_id)
      .set("compute_id", form.compute_id)
      .set("location", form.location)

    return this.http
      .get<JSON>(`${environment.api_url}/graphs/weekday`, { params: params }).pipe(
        tap(_ => this.log('building weekday graph')),
        catchError(this.handleError<JSON>('getWeekdayData', <JSON>{}))
      );
  }

  getHourData(form: SearchForm): Observable<JSON> {
    let params = new HttpParams()
      .set("start_date", form.start_date)
      .set("end_date", form.end_date)
      .set("student_id", form.student_id)
      .set("compute_id", form.compute_id)
      .set("location", form.location)
    return this.http
      .get<JSON>(`${environment.api_url}/graphs/hour`, { params: params }).pipe(
        tap(_ => this.log('building graphs')),
        catchError(this.handleError<JSON>('getHourData', <JSON>{}))
      );
  }
  
  getRawSearchData(form: SearchForm): Observable<Sample[]> {
    let params = new HttpParams()
      .set("start_date", form.start_date)
      .set("end_date", form.end_date)
      .set("student_id", form.student_id)
      .set("compute_id", form.compute_id)
      .set("location", form.location)
    return this.http
      .get<Sample[]>(`${environment.api_url}/graphs/search`, { params: params }).pipe(
        tap(_ => this.log('building search')),
        catchError(this.handleError<Sample[]>('getRawSearchData', <Sample[]>[]))
      );
  }

  // getHourData(form: SearchForm): Observable<JSON> {
  //   let params = new HttpParams().set("start_date",form.start_date).set("end_date", form.end_date); 
  //   return this.http
  //     .get<JSON>(`http://0.0.0.0:5000/v1.0/graphs/hour`,{params: params}).pipe(
  //       tap(_ => this.log('building graphs')),
  //       catchError(this.handleError<JSON>('getHourData', <JSON>{}))
  //     );
  // }

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
  }
}


