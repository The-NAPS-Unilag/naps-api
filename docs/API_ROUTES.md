# NAPS API Routes (Frontend Integration)

This document is the authoritative, frontend-facing route reference derived from the current Flask implementation in `app/routes/`.

**Base URL**
All API routes are mounted under `/api`, except the root `/` and `/health` routes.

**Content Types**
- JSON endpoints: `Content-Type: application/json`
- File uploads: `Content-Type: multipart/form-data`

**Auth Overview**
- JWT auth uses the `Authorization` header: `Bearer <access_token>`.
- Admin endpoints require both JWT and a valid API key header: `x-api-key: <key>`.
- Some admin endpoints require super-admin privileges.

**Standard Error Responses**
- 400: invalid or missing input
- 401: authentication failed or missing
- 403: permission denied
- 404: resource not found
- 409: conflict (e.g., duplicate unique field)
- 500: server error

---

## Public Utility

`GET /`
Returns a simple HTML message.

`GET /health`
Returns `{ status, timestamp, service, database }`.
- 200 if DB is healthy
- 503 if DB is unhealthy

---

## Authentication + Users

`POST /api/users`
Creates a user.
- Auth: none
- Content-Type: `multipart/form-data`
- Required fields: `firstname`, `lastname`, `email`, `current_level`, `matric_no`, `password`
- Optional files: `departmental_fees`, `profile_picture`

Request example:
```bash
curl -X POST /api/users \
  -F firstname=John \
  -F lastname=Doe \
  -F email=john@example.com \
  -F current_level=300 \
  -F matric_no=CSC/2021/001 \
  -F password=securepassword \
  -F profile_picture=@/path/to/pic.jpg
```

`POST /api/users/confirm`
Confirms email with OTP.
- Auth: none
- Body: `{ email, otp }`

`POST /api/users/resend-otp`
Resends verification OTP.
- Auth: none
- Body: `{ email }`

`POST /api/users/login`
Email + password login.
- Auth: none
- Body: `{ email, password }`
- Response: `{ access_token, user }`
- Note: returns 403 if email not confirmed

`POST /api/users/login/matric`
Matric + password login.
- Auth: none
- Body: `{ matric_no, password }`
- Response: `{ access_token, user }`

`GET /api/users/me`
Returns current user details.
- Auth: JWT

`GET /api/users`
Returns paginated users.
- Auth: JWT
- Query: `page` (default 1), `per_page` (default 10)
- Response: `{ users, total, pages, current_page }`

`PUT /api/users/update/<user_id>`
Updates current user profile (self only).
- Auth: JWT
- Content-Type: `multipart/form-data`
- Fields: `current_level?`, `bio?`, `profile_picture?`

`DELETE /api/users/delete/<user_id>`
Deletes current user (self only).
- Auth: JWT

`POST /api/users/forgot-password`
Initiates password reset.
- Auth: none
- Body: `{ email }`

`POST /api/users/reset-password`
Resets password by OTP.
- Auth: none
- Body: `{ email, otp, new_password }`

`GET /api/users/<user_id>/activity`
Returns activity feed for a user.
- Auth: JWT (self or admin)
- Query: `limit` (default 20), `offset` (default 0)

Response example:
```json
{
  "activities": [
    {
      "id": 12,
      "user_id": 5,
      "action": "profile_updated",
      "description": "Updated profile information",
      "created_at": "2026-02-08T10:12:45.123456"
    }
  ]
}
```

---

## API Key Management

`POST /api/generate_api_key`
Generates API key.
- Auth: JWT + Admin
- Response: `{ message, api_key }`

`POST /api/test_generate_api_key`
Unsafe test key generation.
- Auth: none

`GET /api/api_keys`
Lists API keys.
- Auth: JWT + Admin

`DELETE /api/api_keys/<api_key_id>`
Deletes API key.
- Auth: JWT + Admin

---

## Admins

All `/api/admins/*` routes require `x-api-key` + JWT unless noted.

`POST /api/admins/login`
Admin login.
- Auth: `x-api-key` only
- Body: `{ email, password }`
- Response: `{ access_token }`

`POST /api/admins/super-admin`
Creates super admin.
- Auth: `x-api-key` + JWT + Super Admin
- Body: `{ email, password, firstname, lastname }`

`POST /api/admins/admin`
Creates admin.
- Auth: `x-api-key` + JWT + Super Admin
- Body: `{ email, password, firstname, lastname }`

`GET /api/admins/users/<user_id>`
Gets a user.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/users`
Lists users.
- Auth: `x-api-key` + JWT + Admin
- Query: `search?`

`PUT /api/admins/users/<user_id>/deactivate`
Deactivates user.
- Auth: `x-api-key` + JWT + Admin

`PUT /api/admins/users/<user_id>/reactivate`
Reactivates user.
- Auth: `x-api-key` + JWT + Admin

`DELETE /api/admins/users/<user_id>`
Deletes user.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/resources`
Lists resources.
- Auth: `x-api-key` + JWT + Admin
- Query: `status?` (pending, approved, rejected)

`PUT /api/admins/resources/<resource_id>/approve`
Approves resource.
- Auth: `x-api-key` + JWT + Admin

`PUT /api/admins/resources/<resource_id>/reject`
Rejects resource.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/events`
Lists events.
- Auth: `x-api-key` + JWT + Admin
- Query: `status?` (approved, pending)

`PUT /api/admins/events/<event_id>/approve`
Approves event.
- Auth: `x-api-key` + JWT + Admin

`DELETE /api/admins/events/<event_id>/reject`
Rejects event.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/mentee-applications`
Lists mentee applications.
- Auth: `x-api-key` + JWT + Admin
- Query: `status?`

`PUT /api/admins/mentee-applications/<app_id>/approve`
Approves mentee application.
- Auth: `x-api-key` + JWT + Admin

`PUT /api/admins/mentee-applications/<app_id>/reject`
Rejects mentee application.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/mentor-applications`
Lists mentor applications.
- Auth: `x-api-key` + JWT + Admin
- Query: `status?`

`PUT /api/admins/mentor-applications/<app_id>/approve`
Approves mentor application.
- Auth: `x-api-key` + JWT + Admin

`PUT /api/admins/mentor-applications/<app_id>/reject`
Rejects mentor application.
- Auth: `x-api-key` + JWT + Admin

`POST /api/admins/mentorship/pairings`
Creates mentorship pairing.
- Auth: `x-api-key` + JWT + Admin
- Body: `{ mentor_id, mentee_id }`

`GET /api/admins/feedback`
Lists feedback.
- Auth: `x-api-key` + JWT + Admin
- Query: `category?`, `status?`

`PUT /api/admins/feedback/<feedback_id>/status`
Updates feedback status.
- Auth: `x-api-key` + JWT + Admin
- Body: `{ status }`

`GET /api/admins/analytics/summary`
Summary stats.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/analytics/export/users.csv`
Downloads CSV.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/analytics/export/summary.pdf`
Downloads PDF.
- Auth: `x-api-key` + JWT + Admin

`GET /api/admins/audit-logs`
Lists audit logs.
- Auth: `x-api-key` + JWT + Super Admin

---

## Events

Base path: `/api/events`

`GET /api/events/`
Lists approved events.
- Auth: JWT

`GET /api/events/<event_id>`
Gets a single event.
- Auth: JWT

`POST /api/events/`
Creates event.
- Auth: JWT
- JSON body: `{ name, description, date, time, location, event_type, capacity, image_url? }`
- Or multipart form: fields `name`, `description`, `date`, `time`, `location`, `event_type`, `capacity` with optional file `image`
- Notes: If `image` is provided, it is uploaded to Cloudinary and stored as `image_url`.
- `date`: `YYYY-MM-DD`
- `time`: `HH:MM`

`POST /api/events/<event_id>/rsvp`
RSVP to event.
- Auth: JWT

`POST /api/events/<event_id>/cancel_rsvp`
Cancel RSVP.
- Auth: JWT

`GET /api/events/user-rsvps`
Lists events the current user has RSVP’d to.
- Auth: JWT
- Response: `{ events: [<event>] }`

`GET /api/events/type/<event_type>`
Lists events by type.
- Auth: JWT

**Event Object Fields**
- `id`, `name`, `description`, `date`, `time`, `location`, `event_type`, `capacity`
- `image_url`
- `rsvp_count`
- `is_open_for_registration`
- `user_has_rsvpd`

---

## Resources

Base path: `/api/resources`

`POST /api/resources/`
Uploads resource.
- Auth: JWT
- Content-Type: `multipart/form-data`
- Required fields: `title`, `author`, `course_title`, `level`
- Required file: `file`
- Optional: `contributors` (repeatable)

`GET /api/resources/level/<level>`
Lists approved resources for a level.
- Auth: JWT

`GET /api/resources/pending`
Lists pending resources.
- Auth: JWT + Admin

`POST /api/resources/<resource_id>/approve`
Approves resource.
- Auth: JWT + Admin

`DELETE /api/resources/<resource_id>`
Deletes resource and file.
- Auth: JWT + Admin

**Resource Object Fields**
- `id`, `title`, `author`, `course_title`, `level`
- `file_url`, `file_type`, `file_size`
- `contributors`, `uploaded_by`, `status`, `is_approved`, `created_at`

Notes: `file_type` and `file_size` are derived at upload time and may be `null` if unavailable.

---

## Forums

Base path: `/api/forums`

`GET /api/forums/`
Lists forums.
- Auth: none

`POST /api/forums/`
Creates forum.
- Auth: JWT + Admin
- Body: `{ name, description, is_general? }`

`POST /api/forums/<forum_id>/join`
Join a forum.
- Auth: JWT

`POST /api/forums/<forum_id>/threads`
Create a thread.
- Auth: JWT
- Body: `{ title, body }`

`GET /api/forums/threads/<thread_id>`
Get a thread + messages.
- Auth: JWT

`POST /api/forums/threads/<thread_id>/messages`
Post message.
- Auth: JWT
- Content-Type: `multipart/form-data`
- Required: `content`
- Optional: `attachment`, `parent_message_id`

`GET /api/forums/explore`
Lists forums.
- Auth: none

`GET /api/forums/recommended`
Lists recommended forums.
- Auth: none

`GET /api/forums/top-contributors`
Lists top contributors.
- Auth: none

`GET /api/forums/threads/<thread_id>/messages`
Lists messages.
- Auth: none

`POST /api/forums/messages/<message_id>/like`
Likes a message.
- Auth: JWT

**Socket.IO Events**
`join_thread`
Client emits: `{ thread_id, user_id }`
Server emits: `user_joined` to room `thread_<thread_id>`.

`leave_thread`
Client emits: `{ thread_id, user_id }`
Server emits: `user_left` to room `thread_<thread_id>`.

---

## Mentorship

Base path: `/api/mentorship`

`POST /api/mentorship/apply`
Apply as mentee.
- Auth: JWT
- Body: `{ matric_no, level, areas_of_interest }`

`POST /api/mentorship/apply-mentor`
Apply as mentor.
- Auth: JWT
- Body: `{ academic_background, area_of_expertise?, preferred_mode, phone_no?, areas_of_interest?, current_level? }`
- Notes: `phone_no` is optional. If `area_of_expertise` is not provided, `current_level` is used.

`GET /api/mentorship/applications`
List pending mentee applications.
- Auth: JWT + Admin

`GET /api/mentorship/mentor-applications`
List pending mentor applications.
- Auth: JWT + Admin

`POST /api/mentorship/mentor-applications/<application_id>/approve`
Approve mentor application.
- Auth: JWT + Admin

`POST /api/mentorship/mentor-applications/<application_id>/reject`
Reject mentor application.
- Auth: JWT + Admin
- Body: `{ reason }`

`POST /api/mentorship/assign-mentor`
Assign mentor.
- Auth: JWT + Admin
- Body: `{ mentorship_application_id, mentor_id }`

`POST /api/mentorship/schedule-session`
Schedule session.
- Auth: JWT
- Body: `{ mentorship_id, scheduled_time, duration, notes? }`
- Notes: `scheduled_time` must be ISO format.

`POST /api/mentorship/submit-feedback`
Submit feedback.
- Auth: JWT
- Body: `{ session_id, rating, comments? }`

`GET /api/mentorship/my-mentorships`
Get mentorships for current user.
- Auth: JWT
- Notes: Each mentorship object includes `area_of_expertise` when available.

`GET /api/mentorship/mentorships/<mentorship_id>/sessions`
Get sessions for mentorship.
- Auth: JWT
- Requires user to be mentor or mentee for the mentorship.

`POST /api/mentorship/mentorships/<mentorship_id>/complete`
Complete mentorship.
- Auth: JWT
- Only mentor or admin can complete.

---

## Feedback

Base path: `/api/feedback`

`POST /api/feedback/`
Create feedback.
- Auth: JWT
- Body: `{ subject, message, category? }`

---

## Notes For Frontend

- Event `user_has_rsvpd` is computed per request from the current JWT identity.
- Resource `file_type` and `file_size` may be `null` if the upload stream does not expose size.
- Admin endpoints always require `x-api-key` + JWT.
