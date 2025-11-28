import { Component, Input, signal, computed, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatBadgeModule } from '@angular/material/badge';
import { SidebarNavItem } from '../models/sidebar-nav-item.model';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [
    CommonModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatBadgeModule
  ],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss']
})
export class SidebarComponent {
  @Input() applicationTitle: string = 'Application';
  @Input() currentUser: string = 'User';
  @Input() sidebarLinks: SidebarNavItem[] = [];

  private _isOpen = signal(true);
  private _isMobile = signal(false);

  isOpen = this._isOpen.asReadonly();
  
  sideNavMode = computed(() => this._isMobile() ? 'over' : 'side');
  isInMobileMode = computed(() => this._isMobile());

  constructor(private router: Router, private authService: AuthService) {
    this.checkScreenSize();
  }

  @HostListener('window:resize', ['$event'])
  onResize() {
    this.checkScreenSize();
  }

  private checkScreenSize() {
    this._isMobile.set(window.innerWidth < 768);
    if (this._isMobile()) {
      this._isOpen.set(false);
    }
  }

  toggleSideNavigationBar() {
    this._isOpen.set(!this._isOpen());
  }

  openSidebar() {
    this._isOpen.set(true);
  }

  toggleExpanded(item: SidebarNavItem) {
    if (item.items && item.items.length > 0) {
      if (!this._isOpen()) {
        this._isOpen.set(true);
      }
      item.expanded = !item.expanded;
    }
  }

  navigateToLink(item: SidebarNavItem) {
    if (item.url) {
      this.sidebarLinks.forEach(link => {
        link.active = false;
        if (link.items) {
          link.items.forEach(child => child.active = false);
        }
      });
      item.active = true;
      
      this.router.navigate([item.url]);
      
      if (this._isMobile()) {
        this._isOpen.set(false);
      }
    }
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/testing-assistant']);
  }
}