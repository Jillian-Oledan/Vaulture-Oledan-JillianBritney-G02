# Vaulture

A simple web-based password manager built with Django. Users store their private credentials in a personal vault that is locked by a master key. Everything sensitive is encrypted in the browser before it reaches the server.

## Features

- **Accounts:** register with validation (required fields, valid and unique email/username, matching passwords), log in, log out, and clear success/error messages. Passwords are hashed with Django's built-in authentication.
- **Role-based dashboards:** `admin` and `customer` roles. Each role lands on its own dashboard, and typing another role's URL redirects you away.
- **Profile:** view and edit your own name, email, contact number, and photo.
- **Password vault (customer dashboard):**
  - Create a master key on first use and unlock with it on later visits
  - Add, view, edit, and delete logins and secure notes
  - Search by title, show/hide passwords, and copy to clipboard
  - Built-in password generator
- **Admin dashboard:** overview of registered users. The Django admin site is not used as the main panel.

## How the security works

- The master key never leaves the browser and is never stored.
- The browser derives an AES-256-GCM key from it using PBKDF2 and a per-user random salt.
- Usernames, passwords, URLs, and notes are encrypted client-side. The server only stores ciphertext (plus the entry title, used for search).
- Each user can only access their own entries.
- **There is no master key recovery.** If it is forgotten, the vault cannot be decrypted.

## Tech stack

Django (backend and templates)
PostgreSQL via Supabase (or local PostgreSQL)
Web Crypto API
HTML/CSS/JavaScript.
