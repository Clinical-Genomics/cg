"""
These are independent interfaces to tools outside the package.

- "Apps" are NOT allowed to cross-talk directly.
- "Apps" are NOT allowed to use functionality of the main package directly.

All access to functions, classes, exceptions from within the main packages should
go through these "app" interfaces.
"""
