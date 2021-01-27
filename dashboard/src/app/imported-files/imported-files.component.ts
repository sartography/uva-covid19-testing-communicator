import { Component, OnInit } from '@angular/core';
import { IvyFileService } from './ivyfile.service';

import { IvyFile } from './ivyfile';

@Component({
  selector: 'app-imported-files',
  templateUrl: './imported-files.component.html',
  styleUrls: ['./imported-files.component.css']
})
export class ImportedFilesComponent implements OnInit {
  fileList: IvyFile[] = [];
  constructor(private fileService: IvyFileService) { }

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
    this.fileService.getFiles(i).subscribe(fileList => this.fileList = fileList);
  }
}

