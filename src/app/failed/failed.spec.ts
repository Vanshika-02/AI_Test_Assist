import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Failed } from './failed';

describe('Failed', () => {
  let component: Failed;
  let fixture: ComponentFixture<Failed>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Failed]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Failed);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
