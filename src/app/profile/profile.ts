import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environment/environment'; 
import { LoginService } from '../core/services/loginService';


type ProfileType = {
  givenName?: string;
  surname?: string;
  userPrincipalName?: string;
  id?: string;
};

@Component({
  selector: 'app-profile',
  imports: [],
  templateUrl: './profile.html',
  styleUrl: './profile.css',
})

export class Profile implements OnInit {
  profile: ProfileType | undefined;

  constructor(private http: HttpClient,private loginService:LoginService) {}

  ngOnInit() {
    this.loginService.getUserInfo()
  }

  getProfile(url: string) {
    this.http.get(url).subscribe((profile) => {
      this.profile = profile;
    });
  }
}