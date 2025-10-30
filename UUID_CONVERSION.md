# UUID Conversion Summary

## Changes Made

All IDs in the auth module have been converted from Integer to UUID for better scalability and security.

## Modified Files

### 1. Models (`src/domain/auth/models.py`)
- Added custom `UUID` type decorator for cross-database compatibility
- Converted all `id` columns to UUID type:
  - `SecurityQuestion.id`
  - `User.id`
  - `RefreshToken.id`
- Updated foreign key columns to UUID:
  - `User.security_question_id`
  - `RefreshToken.user_id`

### 2. Schemas (`src/domain/auth/schemas.py`)
- Added `UUID` import from `uuid` module
- Updated all ID fields to use `UUID` type:
  - `User.id`
  - `UserCreate.security_question_id`
  - `RefreshToken.id`
  - `RefreshToken.user_id`
  - `RefreshTokenCreate.user_id`
  - `SecurityQuestion.id`

### 3. Repositories (`src/domain/auth/repositories.py`)
- Added `UUID` import
- Updated method signatures to accept UUID parameters:
  - `UserRepository.get_by_id(user_id: UUID)`
  - `UserRepository.update_password(user_id: UUID, ...)`
  - `SecurityQuestionRepository.get_by_id(question_id: UUID)`
  - `RefreshTokenRepository.get_by_user_id(user_id: UUID)`
  - `RefreshTokenRepository.revoke_all_user_tokens(user_id: UUID)`

### 4. Services (`src/domain/auth/services.py`)
- Added `UUID` import
- Updated method signatures:
  - `AuthService.revoke_all_user_tokens(user_id: UUID)`

### 5. Tests (`tests/conftest.py`)
- Updated `test_user` fixture to fetch security questions and use UUID

### 6. Migration Script
- Created `migration_convert_to_uuid.py` for database migration

## Benefits of UUID

1. **Globally Unique**: UUIDs are globally unique, eliminating collision risks
2. **Security**: UUIDs don't reveal sequential information about records
3. **Distributed Systems**: Better suited for microservices and distributed systems
4. **Scalability**: No need for centralized ID generation
5. **Merge-friendly**: Easier to merge data from multiple sources

## Database Compatibility

The custom `UUID` type decorator ensures compatibility with:
- **PostgreSQL**: Uses native UUID type
- **SQLite**: Uses CHAR(36) to store UUID as string
- **MySQL**: Uses CHAR(36) to store UUID as string

## Migration Steps

To apply the UUID changes to your database:

```bash
# Run the migration script (WARNING: This will drop all tables!)
python migration_convert_to_uuid.py

# Or manually recreate the database:
# 1. Backup your data
# 2. Drop all tables
# 3. Run the application to create new tables with UUID columns
# 4. Restore your data (with new UUIDs)
```

## API Changes

### Before (Integer IDs)
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe"
}
```

### After (UUID)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "johndoe"
}
```

## Testing

All tests have been updated to work with UUIDs. Run tests with:

```bash
pytest tests/
```

## Notes

- UUIDs are stored as strings in JSON responses
- Database foreign keys maintain referential integrity with UUIDs
- All UUID generation uses Python's `uuid.uuid4()` for random UUIDs
- The custom UUID type ensures proper conversion between database and Python objects
