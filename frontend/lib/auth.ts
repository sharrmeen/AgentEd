export interface User {
  id: string
  name: string
  email: string
}

// Backend returns flat response, not nested user object
export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: string
  email: string
  name: string
}

export const auth = {
  setToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token)
    }
  },

  getToken(): string | null {
    if (typeof window === "undefined") return null
    return localStorage.getItem("token")
  },

  setUser(user: User) {
    if (typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(user))
    }
  },

  getUser(): User | null {
    if (typeof window === "undefined") return null
    const userStr = localStorage.getItem("user")
    return userStr ? JSON.parse(userStr) : null
  },

  getUserId(): string | null {
    const user = this.getUser()
    return user?.id || null
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  },

  // Handle flat token response from backend
  handleAuthResponse(response: TokenResponse) {
    this.setToken(response.access_token)
    this.setUser({
      id: response.user_id,
      name: response.name,
      email: response.email,
    })
  },

  logout() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      window.location.href = "/login"
    }
  },
}
