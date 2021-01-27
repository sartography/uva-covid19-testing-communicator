import { Component, OnInit } from '@angular/core';
import { DepositService } from './deposit.service';
import { Deposit } from "../deposit";

declare var jQuery: any;

@Component({
  selector: 'app-deposits',
  templateUrl: './deposits.component.html',
  styleUrls: ['./deposits.component.css']
})
export class DepositsComponent implements OnInit {
  depositList: Deposit[] = [];
  newDeposit: Deposit = {
    amount: 0,
    date_added: "",
    notes: ''
  };
  date_temp = new Date(Date.now());

  constructor(
    private depositService: DepositService) {
  }

  addDeposit(): void {
    this.newDeposit.date_added = this.date_temp.toLocaleDateString();

    this.depositService.addDeposit(this.newDeposit).subscribe(deposit => this.depositList.push(deposit))
  }

  current_page: number = 0;
  item_per_page: Number = 10;
  available_pages: Number[] = [];
  
  ngOnInit(): void {
    this.paginateSearch(0);
  }

  paginateSearch(i: number): void {
    this.current_page = i;
    this.available_pages = [];
    for (let i = this.current_page - 10; i < this.current_page + 10; i++){
      if (i > 0){
      this.available_pages.push(i);
      }
    }
    this.depositService.getDeposits(i).subscribe(depositList => this.depositList = depositList);
  }


}
