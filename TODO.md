  ## some explanations below
  1. Deployment works, but runtime is not
  2. Shared hostings disallow symbolic links and private pip installation
  so, we need to do it manually (this ge-pip thing)
  3. We should be mandatory python 3.6
  4. We have problem with psycopg2-binary and psycopg2 at all - it is native drive
  that have system dependent parts. This will not work on shared hosting - use psycopg (pure python implementation)