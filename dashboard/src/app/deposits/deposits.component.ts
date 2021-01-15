import { Component, OnInit } from '@angular/core';
import { DepositService } from '../deposit.service';
import {Deposit} from "../deposit";
@Component({
  selector: 'app-deposits',
  templateUrl: './deposits.component.html',
  styleUrls: ['./deposits.component.css']
})
export class DepositsComponent implements OnInit {
  depositList: Deposit[];
  constructor(
    private depositService: DepositService) {
  }

  getDeposits(): void {
    this.depositService.getDeposits().subscribe(depositList => this.depositList = depositList);
  }

  ngOnInit(): void {
    this.getDeposits();
  }

 
}
