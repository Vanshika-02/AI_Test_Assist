import { Component, OnInit } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { SidebarComponent } from './sidebar/sidebar.component';
import { SidebarNavItem } from './models/sidebar-nav-item.model';
import { AuthService, UserRole } from './auth.service';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, CommonModule, MatIconModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  title = 'Testing Assistant';
  applicationTitle = 'Testing Assistant';
  currentUser = '';
  sidebarLinks: SidebarNavItem[] = [];

  constructor(
    private authService: AuthService,
    private router: Router
  ) {
    console.log('AppComponent constructor');
  }

  ngOnInit() {
    console.log('AppComponent ngOnInit');
    
    if (!this.authService.getCurrentUser()) {
      this.authService.login('Tester1', 'tester');
    }

    this.authService.currentUser$.subscribe(user => {
      console.log('User changed:', user);
      if (user) {
        this.currentUser = user.username;
        this.applicationTitle = this.getTitleForRole(user.role);
        this.updateSidebarLinks(user.role);
      }
    });
  }

  getTitleForRole(role: UserRole): string {
    switch(role) {
      case 'admin': return 'Test Assistant Admin View';
      case 'po': return 'Product Owner View';
      case 'tester': return 'Testing Assistant User';
      default: return 'Testing Assistant';
    }
  }

  getDefaultRouteForRole(role: UserRole): string {
    switch(role) {
      case 'admin': return '/dashboard';
      case 'po': return '/register-product';
      case 'tester': return '/testing-assistant';
      default: return '/testing-assistant';
    }
  }

  switchRole(role: UserRole) {
    console.log('Switching to role:', role);
    const username = role === 'admin' ? 'Admin User' : 
                     role === 'po' ? 'PO User' : 'Tester1';
    
    // Save the role and navigate
    this.authService.login(username, role);
    const route = this.getDefaultRouteForRole(role);
    
    // Navigate then reload
    this.router.navigate([route]).then(() => {
      window.location.reload();
    });
  }

  private updateSidebarLinks(role: UserRole) {
    console.log('Updating sidebar for role:', role);
    
    if (role === 'admin') {
      this.sidebarLinks = [
        { id: 'dashboard', title: 'Dashboard', url: '/dashboard', icon: 'dashboard', active: false },
        { id: 'onboard-product', title: 'Onboard New Product', url: '/onboard-product', icon: 'add_circle', active: false }
      ];
    } else if (role === 'po') {
      this.sidebarLinks = [
        { id: 'register-product', title: 'Register Product', url: '/register-product', icon: 'app_registration', active: false }
      ];
    } else {
      this.sidebarLinks = [
        { id: 'testing-assistant', title: 'Testing Assistant', url: '/testing-assistant', icon: 'science', active: false }
      ];
    }
    
    console.log('Sidebar links updated:', this.sidebarLinks);
  }
}