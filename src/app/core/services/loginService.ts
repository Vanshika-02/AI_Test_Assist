import { HttpClient } from '@angular/common/http';
import { Inject, Injectable } from '@angular/core';
import {
  MSAL_GUARD_CONFIG,
  MsalBroadcastService,
  MsalGuardConfiguration,
  MsalService,
} from '@azure/msal-angular';
import {
  AccountInfo,
  EventMessage,
  EventType,
  RedirectRequest,
} from '@azure/msal-browser';

import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';


@Injectable({
  providedIn: 'root',
})
export class LoginService {
  loginDisplay$ = new BehaviorSubject<boolean>(false);
  private userIdSubject = new BehaviorSubject<string | null>(null);
  userId$ = this.userIdSubject.asObservable();
  constructor(
    private authService: MsalService,
    @Inject(MSAL_GUARD_CONFIG) private msalGuardConfig: MsalGuardConfiguration,
    private msalBroadcastService: MsalBroadcastService,
    private http: HttpClient
  ) {
    this.listenForLogin();
    this.loadUserId();
  }
  private listenForLogin() {
    this.msalBroadcastService.msalSubject$.subscribe((event: EventMessage) => {
      if (event.eventType === EventType.LOGIN_SUCCESS) {
        this.loadUserId();
      }
    });
  }

  private loadUserId() {
    let account = this.authService.instance.getActiveAccount();
    if (!account) {
      const accounts = this.authService.instance.getAllAccounts();
      if (accounts.length > 0) {
        this.authService.instance.setActiveAccount(accounts[0]);
        account = accounts[0];
      }
    }
    if (account) {
      this.userIdSubject.next(account.username.split('@')[0]);
    }
  }

  getNtId(): string | null {
    return this.userIdSubject.getValue();
  }

  setLoginDisplay() {
    const accounts = this.authService.instance.getAllAccounts();
    this.loginDisplay$.next(accounts.length > 0);
  }

  loginRedirect() {
    if (this.msalGuardConfig.authRequest) {
      this.authService.loginRedirect({
        ...this.msalGuardConfig.authRequest,
      } as RedirectRequest);
    } else {
      this.authService.loginRedirect();
    }
  }

  logout(popup?: boolean) {
    if (popup) {
      this.authService.logoutPopup({
        mainWindowRedirectUri: '/',
      });
    } else {
      this.authService.logoutRedirect();
    }
  }
  getUserId(): any {
    const account: AccountInfo | null =
      this.authService.instance.getActiveAccount();
    if (account) {
      return account.name;
    }
    return null;
  }

  getUserInfo(): any {
    const account: AccountInfo | null =
      this.authService.instance.getActiveAccount();
    if (account) {
      return console.log(account);
    }
    return null;
  }


  getUserDept(original:boolean=false): string {

    const account: AccountInfo | null =
      this.authService.instance.getActiveAccount();
    if (account && account.name) {
      // Extract text inside parentheses and remove numerical values
      const match = account.name.match(/\(([^)]+)\)/); // Extract text inside parentheses
      if (match && ! original)  {
        const cleanedText = match[1].replace(/\d+/g, ''); // Remove numerical values
        return cleanedText.split(' ')[0]; // Return the first part
      }
      else{
        return match?match[1]:"";
      }
    }
    return '';
  }

  setLoginDisplay1() {
    return this.authService.instance.getAllAccounts().length > 0;
  }
}
