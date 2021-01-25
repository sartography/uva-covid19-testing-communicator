import { TestBed } from '@angular/core/testing';

import { IvyfileService } from './ivyfile.service';

describe('IvyfileService', () => {
  let service: IvyfileService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(IvyfileService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
