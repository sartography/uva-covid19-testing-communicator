import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DepositsComponent } from './deposits/deposits.component';
import { GraphsComponent } from './graphs/graphs.component';
import { ImportedFilesComponent} from './imported-files/imported-files.component'

const routes: Routes = [
  { path: 'deposits', component: DepositsComponent },
  { path: 'imports', component: ImportedFilesComponent },
  { path: 'graphs', component: GraphsComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }