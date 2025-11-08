# OAuth Authentication Setup Guide

This guide will help you configure OAuth authentication for your Scanner Server instance. With OAuth enabled, only authorized users can access your scanner server.

## Table of Contents

- [Overview](#overview)
- [Supported Providers](#supported-providers)
- [Quick Start](#quick-start)
- [Provider-Specific Setup](#provider-specific-setup)
  - [Google OAuth](#google-oauth)
  - [GitHub OAuth](#github-oauth)
  - [Azure AD OAuth](#azure-ad-oauth)
  - [Custom OAuth Provider](#custom-oauth-provider)
- [Configuration](#configuration)
- [Access Control](#access-control)
- [Troubleshooting](#troubleshooting)

## Overview

Scanner Server supports OAuth 2.0 authentication with multiple providers. When enabled, users must authenticate through your chosen OAuth provider before accessing the application.

## Supported Providers

- **Google** - Use Google accounts for authentication
- **GitHub** - Use GitHub accounts for authentication
- **Azure AD** - Use Microsoft Azure Active Directory
- **Custom** - Any OAuth 2.0 compliant provider

## Quick Start

1. **Choose an OAuth Provider** and register your application
2. **Get OAuth Credentials** (Client ID and Client Secret)
3. **Configure Scanner Server** through the Settings page
4. **Set Allowed Users** (optional - leave empty to allow all authenticated users)
5. **Test the Configuration** using the "Test OAuth Config" button
6. **Enable OAuth** by checking the "Enable OAuth Authentication" checkbox
7. **Save Settings**

## Provider-Specific Setup

### Google OAuth

#### 1. Create OAuth Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Choose **Web application** as the application type
6. Set the **Authorized redirect URIs**:
   - `http://localhost:5000/auth/callback` (for local development)
   - `https://yourdomain.com/auth/callback` (for production)

#### 2. Configure in Scanner Server

1. Navigate to Settings page
2. In OAuth Authentication section:
   - **Enable OAuth**: ✓ Checked
   - **OAuth Provider**: Google
   - **Client ID**: Your Google OAuth Client ID
   - **Client Secret**: Your Google OAuth Client Secret
   - **Redirect URI**: Must match what you configured in Google Console
   - **Scope**: `openid profile email` (default)
   - **Allowed Users**: Add email addresses (one per line) or leave empty

### GitHub OAuth

#### 1. Create OAuth Application

1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** > **New OAuth App**
3. Fill in the application details:
   - **Application name**: Scanner Server
   - **Homepage URL**: `http://localhost:5000` or your domain
   - **Authorization callback URL**: `http://localhost:5000/auth/callback`
4. Click **Register application**
5. Generate a new client secret

#### 2. Configure in Scanner Server

1. Navigate to Settings page
2. In OAuth Authentication section:
   - **Enable OAuth**: ✓ Checked
   - **OAuth Provider**: GitHub
   - **Client ID**: Your GitHub OAuth App Client ID
   - **Client Secret**: Your GitHub OAuth App Client Secret
   - **Redirect URI**: Must match your callback URL
   - **Allowed Users**: Add GitHub email addresses

### Azure AD OAuth

#### 1. Register Application in Azure

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: Scanner Server
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: Web - `http://localhost:5000/auth/callback`
5. After registration, note the **Application (client) ID** and **Directory (tenant) ID**
6. Go to **Certificates & secrets** > **New client secret**
7. Create and copy the secret value

#### 2. Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** > **Microsoft Graph**
3. Add these delegated permissions:
   - `openid`
   - `profile`
   - `email`
   - `User.Read`

#### 3. Configure in Scanner Server

1. Navigate to Settings page
2. In OAuth Authentication section:
   - **Enable OAuth**: ✓ Checked
   - **OAuth Provider**: Azure AD
   - **Client ID**: Your Application (client) ID
   - **Client Secret**: Your client secret value
   - **Azure Tenant ID**: Your Directory (tenant) ID (or "common" for multi-tenant)
   - **Redirect URI**: Must match your redirect URI in Azure
   - **Allowed Users**: Add Azure AD email addresses

### Custom OAuth Provider

For any OAuth 2.0 compliant provider (e.g., Keycloak, Auth0, Okta, etc.):

#### 1. Configure in Scanner Server

1. Navigate to Settings page
2. In OAuth Authentication section:
   - **Enable OAuth**: ✓ Checked
   - **OAuth Provider**: Custom Provider
   - **Client ID**: Your OAuth application client ID
   - **Client Secret**: Your OAuth application client secret
   - **Authorization URL**: OAuth authorization endpoint (e.g., `https://auth.example.com/oauth/authorize`)
   - **Token URL**: OAuth token endpoint (e.g., `https://auth.example.com/oauth/token`)
   - **User Info URL**: OAuth userinfo endpoint (e.g., `https://auth.example.com/oauth/userinfo`)
   - **Redirect URI**: `http://localhost:5000/auth/callback`
   - **Scope**: Space-separated scopes (e.g., `openid profile email`)
   - **Allowed Users**: Add email addresses

## Configuration

### Configuration File

OAuth settings are stored in `/app/config/config.json`:

```json
{
  "oauth": {
    "enabled": true,
    "provider": "google",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "authorization_url": "",
    "token_url": "",
    "userinfo_url": "",
    "redirect_uri": "http://localhost:5000/auth/callback",
    "scope": "openid profile email",
    "allowed_users": [
      "user1@example.com",
      "user2@example.com"
    ]
  }
}
```

### Environment Variables

You can also set OAuth configuration via environment variables (recommended for production):

```bash
# Set in docker-compose.yml or .env file
OAUTH_ENABLED=true
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=https://scanner.example.com/auth/callback
```

## Access Control

### Allowed Users

The `allowed_users` setting controls who can access your Scanner Server:

- **Empty list**: All authenticated users from your OAuth provider can access
- **With emails**: Only specified email addresses can access

Example configuration for restricted access:

```json
"allowed_users": [
  "admin@company.com",
  "scanner-user@company.com"
]
```

### User Experience

1. **Unauthenticated users** see a login page
2. **Click "Sign In with OAuth"** to start authentication
3. **OAuth provider** handles authentication
4. **Authorized users** are redirected to the Scanner Server home page
5. **Unauthorized users** see an error message

## Troubleshooting

### Common Issues

#### 1. Redirect URI Mismatch

**Error**: `redirect_uri_mismatch` or similar

**Solution**: Ensure the Redirect URI in Scanner Server settings **exactly matches** the one configured in your OAuth provider.

#### 2. Invalid Client ID/Secret

**Error**: `invalid_client`

**Solution**: Double-check your Client ID and Client Secret. Regenerate if necessary.

#### 3. User Not Authorized

**Error**: "Your account is not authorized to access this application"

**Solution**: Add the user's email address to the `allowed_users` list in settings, or leave it empty to allow all users.

#### 4. HTTPS Required

**Error**: Some providers require HTTPS for redirect URIs

**Solution**:
- For production, use HTTPS with a valid SSL certificate
- For development, check if your provider allows `http://localhost`

#### 5. Scope Issues

**Error**: Missing user information after login

**Solution**: Ensure your OAuth application has the correct scopes/permissions:
- Google: `openid profile email`
- GitHub: `user:email`
- Azure: `openid profile email User.Read`

### Testing OAuth Configuration

Use the **Test OAuth Config** button in the Settings page to validate your configuration before enabling OAuth.

### Logs

Check the application logs for detailed error messages:

```bash
docker-compose logs -f scanner-server
```

## Security Best Practices

1. **Use HTTPS in Production**: Always use HTTPS for your Scanner Server in production
2. **Secure Client Secret**: Never commit your client secret to version control
3. **Use Environment Variables**: Store sensitive credentials in environment variables
4. **Restrict Allowed Users**: Use the allowed users list to limit access
5. **Regular Secret Rotation**: Rotate OAuth client secrets periodically
6. **Monitor Access**: Check application logs for unauthorized access attempts

## Disabling OAuth

To disable OAuth authentication:

1. Go to Settings page
2. Uncheck **Enable OAuth Authentication**
3. Click **Save All Settings**

The application will immediately become accessible without authentication.

## Support

For issues or questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review application logs
3. Open an issue on the GitHub repository

---

**Note**: After changing OAuth settings, you may need to clear your browser cookies or use an incognito window to test the new configuration.
