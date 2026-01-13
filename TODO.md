# TODO - Journal App Features & Improvements

## Future Features
- [ ] Implement email service for password reset (SendGrid, AWS SES, or Gmail SMTP)
  - Add email configuration to `.env`
  - Update `/forgot` route to send reset token via email instead of displaying on-screen
  - Create email templates for password reset
  
- [ ] Implement Google OAuth login
  - Set up OAuth app credentials on Google Cloud Console
  - Install Flask-Login extension
  - Add OAuth callback handling
  - Update User model to support OAuth provider tracking
  - Add "Sign in with Google" button to login page

- [ ] Add user profile management
- [ ] Implement two-factor authentication (2FA)
- [ ] Implement import Google Doc or .txt to journal entries
- [ ] Add entry sharing/collaboration features
- [ ] Mobile app version

## Security & Input Validation
- [ ] Configure persistent rate limit storage for production (Redis recommended)
  - Currently using in-memory storage (not ideal for multiple servers)

## Code Quality & Maintenance
- [ ] Add comprehensive error handling and logging

## Testing & Verification
- [ ] Test password reset flow end-to-end in production
- [ ] Test Google OAuth flow once implemented
- [ ] Verify email delivery for reset tokens


---