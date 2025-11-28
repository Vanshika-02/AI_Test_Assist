import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TicketDetail {
  id: number;
  ticket_id: string;
  title: string;
  module?: string;
  project_id: number;
  file_path?: string;
  steps?: { num: number; text: string }[];
  created_at?: string;
}

export interface ExecutionResponse {
  execution_id: string;
  ticket_id: string;
  status: string;
  message: string;
  script_path?: string;
}

export interface ExecutionStatus {
  execution_id: string;
  ticket_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  overall_status?: 'PASSED' | 'FAILED' | 'UNKNOWN';
  message: string;
  current_step?: string;
  steps_completed: number;
  steps_total: number;
  started_at?: string;
  completed_at?: string;
  report_path?: string;
  script_path?: string;
  video_path?: string;
}

export interface ScriptInfo {
  filename: string;
  path: string;
  created: string;
  size: number;
}

export interface ScriptsListResponse {
  ticket_id: string;
  scripts_count: number;
  scripts: ScriptInfo[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api';  // Update with your backend URL

  constructor(private http: HttpClient) {}

  /**
   * Get ticket details by ticket ID
   */
  getTicketDetails(ticketId: string): Observable<TicketDetail> {
    return this.http.get<TicketDetail>(`${this.apiUrl}/tickets/${ticketId}`);
  }

  /**
   * Run test for a ticket (generate and execute)
   */
  runTest(ticketId: string): Observable<ExecutionResponse> {
    const params = new HttpParams().set('ticket_id', ticketId);
    return this.http.post<ExecutionResponse>(`${this.apiUrl}/execute-test`, null, { params });
  }

  /**
   * Rerun test for a ticket (using existing script)
   */
  rerunTest(ticketId: string): Observable<ExecutionResponse> {
    const params = new HttpParams().set('ticket_id', ticketId);
    return this.http.post<ExecutionResponse>(`${this.apiUrl}/rerun-test`, null, { params });
  }

  /**
   * Check if scripts exist for a ticket
   */
  listScripts(ticketId: string): Observable<ScriptsListResponse> {
    return this.http.get<ScriptsListResponse>(`${this.apiUrl}/scripts/${ticketId}`);
  }

  /**
   * Get execution status (for polling)
   */
  getExecutionStatus(executionId: string): Observable<ExecutionStatus> {
    return this.http.get<ExecutionStatus>(`${this.apiUrl}/execution-status/${executionId}`);
  }

  /**
   * Download HTML report
   */
  downloadReport(executionId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download-report/${executionId}`, {
      responseType: 'blob'
    });
  }

  /**
   * Download Playwright script
   */
  downloadScript(executionId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download-script/${executionId}`, {
      responseType: 'blob'
    });
  }

  /**
   * Download test video
   */
  downloadVideo(executionId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download-video/${executionId}`, {
      responseType: 'blob'
    });
  }
}
