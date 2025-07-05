# Dashboard Metrics

The admin dashboard now displays two charts powered by Chart.js.

- **User Registrations** – shows daily sign ups for the last 7 days. Registration dates are derived from the first email confirmation token created for each user.
- **Content Distribution** – total number of posts, notes, comments and purchases stored in the database.

These metrics are queried in `admin_routes.dashboard` and passed as JSON variables to the template so the charts update automatically.
