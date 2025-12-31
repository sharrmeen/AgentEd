const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private getAuthToken(): string | null {
    if (typeof window === "undefined") return null
    return localStorage.getItem("token")
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getAuthToken()

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    }

    const config: RequestInit = {
      ...options,
      headers,
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, config)

      if (!response.ok) {
        // Handle 401 - redirect to login
        if (response.status === 401) {
          if (typeof window !== "undefined") {
            localStorage.removeItem("token")
            localStorage.removeItem("user")
            window.location.href = "/login"
          }
          throw new Error("Session expired. Please login again.")
        }

        const error: ApiError = await response.json().catch(() => ({
          detail: "An error occurred",
        }))
        
        // Handle validation errors array
        if (Array.isArray(error.detail)) {
          throw new Error(error.detail.map(e => e.msg).join(", "))
        }
        throw new Error(error.detail || `HTTP ${response.status}`)
      }

      const contentType = response.headers.get("content-type")
      if (contentType && contentType.includes("application/json")) {
        return await response.json()
      }

      return {} as T
    } catch (error) {
      console.error("[API] Request failed:", error)
      throw error
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" })
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" })
  }

  async uploadFile<T>(endpoint: string, file: File, additionalParams?: Record<string, string>): Promise<T> {
    const token = this.getAuthToken()
    const formData = new FormData()
    formData.append("file", file)

    // Build URL with query params if provided
    let url = `${this.baseUrl}${endpoint}`
    if (additionalParams) {
      const params = new URLSearchParams(additionalParams)
      url += `?${params.toString()}`
    }

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    })

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("token")
          localStorage.removeItem("user")
          window.location.href = "/login"
        }
        throw new Error("Session expired. Please login again.")
      }

      const error: ApiError = await response.json().catch(() => ({
        detail: "Upload failed",
      }))
      
      if (Array.isArray(error.detail)) {
        throw new Error(error.detail.map(e => e.msg).join(", "))
      }
      throw new Error(error.detail as string)
    }

    return await response.json()
  }
}

export const api = new ApiClient()
