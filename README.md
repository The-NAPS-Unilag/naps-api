# NAPS API DOCS

This document outlines all available API routes in the project, organized by user role and resource type.

## Table of Contents
- [Overview](#overview)
- [Authentication & Authorization](#authentication--authorization)
- [User Routes](#user-routes)
- [Event Routes](#event-routes)
- [Resource Routes](#resource-routes)
- [Forum Routes](#forum-routes)
- [Mentorship Routes](#mentorship-routes)
- [Admin Routes](#admin-routes)

## Overview

All API routes begin with `/api` prefix. The API uses JWT authentication and requires API keys for most operations.

## Authentication & Authorization

### API Keys
| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/generate_api_key` | Admin | Generate a new API key |
| POST | `/test_generate_api_key` | Any | Generate a test API key (development only) |
| GET | `/api_keys` | Admin | List all API keys |
| DELETE | `/api_keys/<api_key_id>` | Admin | Delete an API key |

## User Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/users` | Any | Create a new user account |
| POST | `/users/login` | Any | User login with email and password |
| POST | `/users/login/matric` | Any | User login with matric number |
| GET | `/users/<user_id>` | Authenticated | Get user details |
| GET | `/users` | Authenticated | List all users (paginated) |
| PUT | `/users/update/<user_id>` | Self | Update user profile |
| DELETE | `/users/delete/<user_id>` | Self | Delete user account |
| POST | `/users/confirm` | Any | Confirm user email with OTP |
| POST | `/users/resend-otp` | Any | Resend verification OTP |
| POST | `/users/forgot-password` | Any | Initiate password reset |
| POST | `/users/reset-password` | Any | Reset password with OTP |

## Event Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| GET | `/api/events/` | Authenticated | Get all approved events |
| GET | `/api/events/<event_id>` | Authenticated | Get details of a specific event |
| POST | `/api/events/` | Authenticated | Create a new event |
| POST | `/api/events/<event_id>/rsvp` | Authenticated | RSVP to an event |
| POST | `/api/events/<event_id>/cancel_rsvp` | Authenticated | Cancel an RSVP for an event |
| GET | `/api/events/type/<event_type>` | Authenticated | Get events filtered by type |

## Resource Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/resources/` | Authenticated | Upload a new resource |
| GET | `/api/resources/level/<level>` | Authenticated | Get resources by academic level |
| GET | `/api/resources/pending` | Admin | Get resources pending approval |
| POST | `/api/resources/<resource_id>/approve` | Admin | Approve a resource |
| DELETE | `/api/resources/<resource_id>` | Admin | Delete a resource |

## Forum Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| GET | `/api/forums/` | Any | Get all forums |
| POST | `/api/forums/` | Admin | Create a new forum |
| POST | `/api/forums/<forum_id>/join` | Authenticated | Join a forum |
| POST | `/api/forums/<forum_id>/threads` | Authenticated | Create a new thread in a forum |
| POST | `/api/forums/threads/<thread_id>/messages` | Authenticated | Send a message in a thread |
| GET | `/api/forums/threads/<thread_id>/messages` | Any | Get all messages in a thread |
| POST | `/api/forums/messages/<message_id>/like` | Authenticated | Like a message |

## Mentorship Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/api/mentorship/apply` | Authenticated | Apply for mentorship as a student |
| POST | `/api/mentorship/apply-mentor` | Authenticated | Apply to become a mentor |
| GET | `/api/mentorship/applications` | Admin | Get pending mentorship applications |
| GET | `/api/mentorship/mentor-applications` | Admin | Get pending mentor applications |
| POST | `/api/mentorship/mentor-applications/<application_id>/approve` | Admin | Approve a mentor application |
| POST | `/api/mentorship/mentor-applications/<application_id>/reject` | Admin | Reject a mentor application |
| POST | `/api/mentorship/assign-mentor` | Admin | Assign a mentor to a student |
| POST | `/api/mentorship/schedule-session` | Authenticated | Schedule a mentorship session |
| POST | `/api/mentorship/submit-feedback` | Authenticated | Submit feedback for a session |
| GET | `/api/mentorship/my-mentorships` | Authenticated | Get user's mentorship relationships |
| GET | `/api/mentorship/mentorships/<mentorship_id>/sessions` | Authenticated | Get all sessions for a mentorship |
| POST | `/api/mentorship/mentorships/<mentorship_id>/complete` | Mentor/Admin | Mark a mentorship as completed |

## Admin Routes

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| POST | `/admin/create` | API Key Required | Create admin user |
| POST | `/admin/login` | API Key Required | Login admin |

## Home Route

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| GET | `/` | Any | Display welcome message and link to Swagger docs |