import { Component, OnInit } from '@angular/core';
import { ChartOptions, ChartType, ChartDataSets } from 'chart.js';

import { Label } from 'ng2-charts';
import { GraphService } from './graph.service'
import { Sample } from '../sample'
import { SearchForm } from '../search_form'

import * as pluginDataLabels from 'chartjs-plugin-datalabels';

@Component({
  selector: 'app-graphs',
  templateUrl: './graphs.component.html',
  styleUrls: ['./graphs.component.css']
})
export class GraphsComponent implements OnInit {

  constructor(private graphService: GraphService) { }

  topBarData: Array<Number> = [0, 0, 0, 0, 0, 0, 0];
  ChartName: String = "Location Activity";
  dailyChartLabels: Label[] = [];
  weekdayChartLabels: Label[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  hourlyChartLabels: Label[] = ["1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 AM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM", "12 PM"];
  dailyChartsData: ChartDataSets[] = [];
  hourlyChartsData: ChartDataSets[] = [];
  weekdayChartsData: ChartDataSets[] = [];

  barChartPlugins = [pluginDataLabels];
  barChartOptions: ChartOptions = {
    responsive: true,
    // We use these empty structures as placeholders for dynamic theming.
    scales: {
      xAxes: [{
        ticks: {
          beginAtZero: true
        },
        stacked: true
      }],
      yAxes: [{
        ticks: {
          beginAtZero: true
        },
        stacked: true
      }]
    },
    legend: {
      onClick: (e, i) => {
        this.form.location = String(i.text);
        this.updateGraphData();
      }
    },
    plugins: {
      datalabels: {

        rotation: -45,
        anchor: 'end',
        align: 'end',
        formatter: (value: any, ctx: any) => {

          let datasets = ctx.chart.data.datasets;
          if (datasets.indexOf(ctx.dataset) === datasets.length - 1) {
            let sum = 0;
            datasets.map((dataset: any) => {
              sum += dataset.data[ctx.dataIndex];
            });
            return sum;
          } else {
            return '';
          }
        }
      }
    }, layout: {
      padding: {
        left: 0,
        right: 20,
        top: 30,
        bottom: 0
      }
    }
  };

  arrayOne(n: number): any[] {
    return Array(n);

  }

  tempData: JSON = <JSON>{};

  searchResult: Sample[] = [];

  start_date: Date = new Date();
  end_date: Date = new Date();

  start_date_1: string = "";
  end_date_1: string = "";
  start_date_2: string = "";
  end_date_2: string = "";

  current_page: number = 0;
  item_per_page: Number = 10;
  available_pages: Number[] = [];
  
  paginateSearch(i: number): void {
    this.current_page = i;
    this.available_pages = [];
    for (let i = this.current_page - 10; i < this.current_page + 10; i++){
      if (i > 0){
      this.available_pages.push(i);
      }
    }
    this.graphService.getRawSearchData(this.form, this.current_page).subscribe(searchResult => this.searchResult = searchResult);
  }

  form: SearchForm = {
    start_date: "",
    end_date: "",
    student_id: "",
    location: "",
    compute_id: "",
    include_tests: false
  };

  
  searchToday(): void {
    this.start_date = new Date();
    this.end_date = new Date();
    this.updateGraphData();
  }
  searchAll(): void {
    this.start_date = new Date(2020,9,5);
    this.end_date = new Date();
    this.updateGraphData();
  }

  updateGraphData(): void {

    if (this.form.location.trim().split(" ").length == 1) {
      this.ChartName = "Total Samples per Station @ Location " + this.form.location;
    } else {
      this.ChartName = "Total Samples per Location";
    }
    if (this.form.location.trim() == "") {
      this.ChartName = "Total Samples per Location";
    }

    this.form.start_date = this.start_date.toLocaleDateString();
    this.form.end_date = this.end_date.toLocaleDateString();

    var date = new Date();
    var date_2 = new Date();

    date.setDate(this.start_date.getDate() - 7);
    this.start_date_1 = date.toLocaleDateString();

    date_2.setDate(this.end_date.getDate() - 7);
    this.end_date_1 = date_2.toLocaleDateString();

    date.setDate(date.getDate() - 7);
    this.start_date_2 = date.toLocaleDateString();

    date_2.setDate(date_2.getDate() - 7);
    this.end_date_2 = date_2.toLocaleDateString();

    var temp = new Date(this.start_date.getTime());
    this.dailyChartLabels = [];
    while (true) {
      this.dailyChartLabels.push(temp.toLocaleDateString());
      if (temp.toLocaleDateString() == this.end_date.toLocaleDateString()) {
        break;
      } else {
        temp.setDate(temp.getDate() + 1);
      }
    }

    this.graphService.getDayData(this.form).subscribe(tempData => {
      this.tempData = tempData;
      this.dailyChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.dailyChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'a' })
      });
    });

    this.graphService.getWeekdayData(this.form).subscribe(tempData => {
      this.tempData = tempData;
      this.weekdayChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.weekdayChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'a' })
      });
    });

    this.graphService.getHourData(this.form).subscribe(tempData => {
      this.tempData = tempData;
      this.hourlyChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.hourlyChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'c' })
      });
    });

    this.graphService.getTopBarData(this.form).subscribe(tempData => {
      this.topBarData = tempData;
    });

    this.paginateSearch(0);
  }

  ngOnInit(): void {
    var end_date = new Date();
    var start_date = new Date();
    this.form.start_date = start_date.toLocaleDateString();
    this.form.end_date = end_date.toLocaleDateString();
    this.updateGraphData();
  }

  chartClicked(e: any): void {
    if (e.active.length > 0) {
      const chart = e.active[0]._chart;
      const activePoints = chart.getElementAtEvent(e.event);
      if (activePoints.length > 0) {
        // get the internal index of slice in pie chart
        const clickedElementIndex = activePoints[0]._index;
        const label = chart.data.labels[clickedElementIndex];
        // get value by index
        const value = chart.data.datasets[0].data[clickedElementIndex];
        console.log(clickedElementIndex, label, value)
        // this.updateGraphData();
      }
    }
  }

}
