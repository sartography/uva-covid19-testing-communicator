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

  public dailyChartLabels: Label[] = [];
  public weekdayChartLabels: Label[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  public hourlyChartLabels: Label[] = ["1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 AM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM", "12 PM"];

  public barChartPlugins = [pluginDataLabels];
  public barChartOptions: ChartOptions = {
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
        top: 20,
        bottom: 0
      }
    }
  };

  public dailyChartsData: ChartDataSets[] = [];
  public hourlyChartsData: ChartDataSets[] = [];
  public weekdayChartsData: ChartDataSets[] = [];

  public tempData: JSON = <JSON>{};

  searchResult: Sample[] = [];

  public start_date: Date = new Date();
  public end_date: Date = new Date();

  public form: SearchForm = {
    start_date: "",
    end_date: "",
    student_id: "",
    location: "",
    compute_id: "",
    include_tests: false
  };

  updateGraphData(): void {

    this.form.start_date = this.start_date.toLocaleDateString();
    this.form.end_date = this.end_date.toLocaleDateString();

    var temp = this.start_date;
    this.dailyChartLabels = [];
    while (true){
      this.dailyChartLabels.push(temp.toLocaleDateString());
      if (temp.toLocaleDateString() == this.end_date.toLocaleDateString()){
        break;
      } else {
        temp.setDate(temp.getDate() + 1);
      }
    }

    this.graphService.getDayData(this.form).subscribe(tempData => {
      this.tempData = tempData
      this.dailyChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.dailyChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'a' })
      });
    });

    this.graphService.getWeekdayData(this.form).subscribe(tempData => {
      this.tempData = tempData
      this.weekdayChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.weekdayChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'a' })
      });
    });

    this.graphService.getHourData(this.form).subscribe(tempData => {
      this.tempData = tempData
      this.hourlyChartsData = [];
      Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
        this.hourlyChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'c' })
      });
    });

    this.graphService.getRawSearchData(this.form).subscribe(searchResult => this.searchResult = searchResult);

    // overall_totals_data = overall_totals_data,
    // this.graphService.getHourData(this.form).subscribe( tempData => {
    //   this.tempData = tempData
    //   this.hourlyChartsData = [];
    //   Object.entries(this.tempData).forEach(([loc_or_stat_name, totals]) => {
    //     this.hourlyChartsData.push({ data: totals, label: loc_or_stat_name, stack: 'a'} )
    //   });
    // });
  }

  ngOnInit(): void {
    var end_date = new Date();
    var start_date = new Date();
    // start_date.setDate(end_date.getDate() - 1);
    this.form.start_date = start_date.toLocaleDateString();
    this.form.end_date = end_date.toLocaleDateString();
    this.updateGraphData();
  }

  public chartClicked(e: any): void {
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
