import { Component, OnInit } from '@angular/core';
import { DepositService } from './deposit.service';
import {Deposit} from "../deposit";

declare var jQuery: any;

@Component({
  selector: 'app-deposits',
  templateUrl: './deposits.component.html',
  styleUrls: ['./deposits.component.css']
})
export class DepositsComponent implements OnInit {
  depositList: Deposit[] = [];
  newDeposit: Deposit = {
    amount :0,
    date_added: "",
  notes:''}
  ;
  date_temp = new Date(Date.now());

  constructor(
    private depositService: DepositService) {
  }

  getDeposits(): void {
    this.depositService.getDeposits().subscribe(depositList => this.depositList = depositList);
  }
  addDeposit(): void {
    this.newDeposit.date_added = this.date_temp.toLocaleDateString();
  
    this.depositService.addDeposit(this.newDeposit).subscribe(deposit => this.depositList.push(deposit)) }
  
  ngOnInit(): void {
    this.getDeposits();
  }

 
}
