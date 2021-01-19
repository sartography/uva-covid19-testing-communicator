import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DepositsComponent } from './deposits/deposits.component';
import { GraphsComponent } from './graphs/graphs.component';
import { ImportedFilesComponent } from './imported-files/imported-files.component';
import { HttpClientModule } from '@angular/common/http';
import { ChartsModule } from 'ng2-charts';
import { TopBarComponent } from './top-bar/top-bar.component';
import { IvyFileService } from './ivyfile.service'
import { DepositService } from './deposit.service';
import { FormsModule } from '@angular/forms';
@NgModule({
  declarations: [
    AppComponent,
    DepositsComponent,
    GraphsComponent,
    ImportedFilesComponent,
    TopBarComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    ChartsModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [IvyFileService, DepositService],
  bootstrap: [AppComponent]
})
export class AppModule { }
