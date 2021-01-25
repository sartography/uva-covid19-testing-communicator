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

  getFiles(): void {
    this.fileService.getFiles().subscribe(fileList => this.fileList = fileList);
  }
  ngOnInit(): void {
    this.getFiles();
  }

}

