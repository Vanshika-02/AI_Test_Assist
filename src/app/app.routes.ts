import { Routes } from '@angular/router';
import { RegisterProductComponent } from './register-product/register-product.component';
import { TestGenerationComponent } from './test-generation/test-generation.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { OnboardProductComponent } from './onboard/onboard.component';

export const routes: Routes = [
  { 
    path: '', 
    redirectTo: 'testing-assistant', 
    pathMatch: 'full' 
  },
  { 
    path: 'dashboard', 
    component: DashboardComponent
    // Remove canActivate temporarily
  },
  { 
    path: 'onboard-product', 
    component: OnboardProductComponent
  },
  { 
    path: 'testing-assistant', 
    component: TestGenerationComponent
  },
  { 
    path: 'register-product', 
    component: RegisterProductComponent
  }
];