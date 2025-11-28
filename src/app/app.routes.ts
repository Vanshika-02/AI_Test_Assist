import { RouterModule, Routes } from '@angular/router';
import { Home } from './home/home';
import { NgModule } from '@angular/core';
import { MsalGuard } from '@azure/msal-angular';
import { Profile } from './profile/profile';
import { Failed } from './failed/failed';

export const routes: Routes = [
  {
    path: 'profile',
    component: Profile,
    canActivate: [MsalGuard],
  },
  {
    path: 'home',
    component: Home,
    canActivate: [MsalGuard],
  },
  {
    path: 'login-failed',
    component: Failed,
  },
];

// @NgModule({
//   imports: [
//     RouterModule.forRoot(routes, {
//       scrollPositionRestoration: 'enabled',
//       anchorScrolling: 'enabled',
//     }),
//   ],
//   exports: [RouterModule],
// })
// export class AppRoutingModule {}