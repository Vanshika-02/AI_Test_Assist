import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type UserRole = 'admin' | 'tester' | 'po';

export interface User {
  username: string;
  role: UserRole;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor() {
    const storedUser = localStorage.getItem('currentUser');
    if (storedUser) {
      this.currentUserSubject.next(JSON.parse(storedUser));
    }
  }

  login(username: string, role: UserRole) {
    const user: User = { username, role };
    localStorage.setItem('currentUser', JSON.stringify(user));
    this.currentUserSubject.next(user);
  }

  logout() {
    localStorage.removeItem('currentUser');
    this.currentUserSubject.next(null);
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  getUserRole(): UserRole | null {
    return this.currentUserSubject.value?.role || null;
  }

  isAdmin(): boolean {
    return this.getUserRole() === 'admin';
  }

  isTester(): boolean {
    return this.getUserRole() === 'tester';
  }

  isPO(): boolean {
    return this.getUserRole() === 'po';
  }
}