import { NativeDateAdapter } from '@angular/material/core';


/** Adapts the native JS Date for use with cdk-based components that work with dates. */
export class CustomDateAdapter extends NativeDateAdapter {
  
  getFirstDayOfWeek(): number {
   return 1;
  }

}