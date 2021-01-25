import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DepositsComponent } from './deposits/deposits.component';
import { GraphsComponent } from './graphs/graphs.component';
import { GraphService } from './graphs/graph.service'
import { ImportedFilesComponent } from './imported-files/imported-files.component';
import { HttpClientModule } from '@angular/common/http';
import { ChartsModule } from 'ng2-charts';
import { IvyFileService } from './imported-files/ivyfile.service'
import { DepositService } from './deposits/deposit.service';
import { FormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatDatepickerModule } from '@angular/material/datepicker';

import { MatNativeDateModule } from '@angular/material/core';
@NgModule({
  declarations: [
    AppComponent,
    DepositsComponent,
    GraphsComponent,
    ImportedFilesComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    ChartsModule,
    HttpClientModule,
    FormsModule,
    MatInputModule,
    MatDatepickerModule,
    MatNativeDateModule,
    BrowserAnimationsModule
  ],
  providers: [IvyFileService, DepositService, GraphService, MatDatepickerModule],
  bootstrap: [AppComponent]
})
export class AppModule { }
