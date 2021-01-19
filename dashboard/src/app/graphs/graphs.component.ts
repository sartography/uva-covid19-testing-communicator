import { Component, OnInit } from '@angular/core';
import { ChartOptions, ChartType, ChartDataSets } from 'chart.js';
import { Label } from 'ng2-charts';
import { GraphService} from '../graph.service'
import { Sample } from '../sample' 
import { SearchForm } from '../search_form'

@Component({
  selector: 'app-graphs',
  templateUrl: './graphs.component.html',
  styleUrls: ['./graphs.component.css']
})
export class GraphsComponent implements OnInit {

  constructor(private graphService: GraphService) { }

  public barChartOptions = {
    scaleShowVerticalLines: false,
    responsive: true
  };
  public dailyChartLabels: Label[] = [];
  public weekdayChartLabels: Label[] = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  public hourlyChartLabels: Label[] = ["1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", "12 AM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM", "12 PM"];

  // public search_result:;
  public barChartLabels: Label[] = ['2006', '2007', '2008', '2009', '2010', '2011', '2012'];
  
  public barChartLegend = true;
  public barChartPlugins = [];

  public dailyChartsData: ChartDataSets[][] = [];
  public hourlyChartsData: ChartDataSets[][] = [];
  public weeklyChartsData: ChartDataSets[][] = [];
  
  currentDate = new Date();
  public barChartData: ChartDataSets[] = [
    { data: [65, 59, 80, 81, 56, 55, 40], label: 'Series A', stack: 'a' },
    { data: [28, 48, 40, 19, 86, 27, 90], label: 'Series B', stack: 'a' }
  ];
  public searchResult: Sample[] = [];
  updateGraphData(): void{
    // chart_ticks = chart_ticks,

    // overall_chart_data = overall_chart_data,
    // daily_charts_data = daily_charts_data,
    // hourly_charts_data = hourly_charts_data,
    // weekday_charts_data = weekday_charts_data,
    

    // overall_totals_data = overall_totals_data,
    // location_totals_data = location_totals_data,
  }
  ngOnInit(): void {

  }

}
