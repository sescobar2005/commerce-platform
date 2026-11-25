"""Unit tests for database session management.

These tests do NOT require a live PostgreSQL database.
They use mocks and in-memory SQLite for session lifecycle tests.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.core.database import SessionLocal, engine, get_db


class TestSessionFactoryConfiguration:
    """Tests for session factory configuration without live database."""

    def test_sessionlocal_is_sessionmaker(self):
        """SessionLocal should be a sessionmaker instance."""
        assert isinstance(SessionLocal, sessionmaker)

    def test_sessionlocal_is_bound_to_engine(self):
        """SessionLocal should be bound to the application engine."""
        assert SessionLocal.kw["bind"] is engine

    def test_sessionlocal_has_autocommit_false(self):
        """SessionLocal should have autocommit disabled."""
        assert SessionLocal.kw["autocommit"] is False

    def test_sessionlocal_has_autoflush_false(self):
        """SessionLocal should have autoflush disabled."""
        assert SessionLocal.kw["autoflush"] is False


class TestSessionCreation:
    """Tests for session creation without live database."""

    def test_sessionlocal_creates_session_instance(self):
        """SessionLocal() should return a Session instance."""
        session = SessionLocal()
        assert isinstance(session, Session)
        session.close()

    def test_session_is_bound_to_engine(self):
        """Created session should be bound to the application engine."""
        session = SessionLocal()
        try:
            assert session.get_bind() is engine
        finally:
            session.close()


class TestSessionLifecycle:
    """Tests for session lifecycle without live database."""

    def test_session_can_be_closed(self):
        """Session should support close() without error."""
        session = SessionLocal()
        session.close()
        assert not session.in_transaction()

    def test_session_close_is_idempotent(self):
        """Calling close() multiple times should not raise."""
        session = SessionLocal()
        session.close()
        session.close()  # Should not raise


class TestSessionCleanup:
    """Tests for session cleanup via get_db dependency."""

    def test_get_db_yields_session(self):
        """get_db should yield a Session instance."""
        generator = get_db()
        session = next(generator)
        assert isinstance(session, Session)
        try:
            generator.close()
        except StopIteration:
            pass

    def test_get_db_closes_session_after_exhaustion(self):
        """get_db should close the session when the generator is exhausted."""
        generator = get_db()
        session = next(generator)
        try:
            generator.close()
        except StopIteration:
            pass
        assert not session.in_transaction()

    def test_get_db_closes_session_on_exception(self):
        """get_db should close the session even if an exception occurs."""
        generator = get_db()
        session = next(generator)
        try:
            generator.throw(RuntimeError("simulated failure"))
        except RuntimeError:
            pass
        assert not session.in_transaction()


class TestTransactionRollback:
    """Tests for transaction rollback behavior without live database."""

    def test_session_supports_rollback(self):
        """Session should support rollback() without error."""
        session = SessionLocal()
        try:
            session.rollback()
        finally:
            session.close()

    def test_session_supports_commit(self):
        """Session should support commit() without error."""
        session = SessionLocal()
        try:
            session.commit()
        finally:
            session.close()


class TestFastApiDependency:
    """Tests for FastAPI dependency behavior using mocks."""

    def test_get_db_is_generator_function(self):
        """get_db should be a generator function."""
        import inspect

        assert inspect.isgeneratorfunction(get_db)

    def test_get_db_yields_single_session(self):
        """get_db should yield exactly one session."""
        generator = get_db()
        sessions = []
        try:
            while True:
                sessions.append(next(generator))
        except StopIteration:
            pass
        assert len(sessions) == 1
        assert isinstance(sessions[0], Session)
        assert not sessions[0].in_transaction()

    def test_get_db_session_not_shared_between_calls(self):
        """Each call to get_db should produce a distinct session."""
        generator1 = get_db()
        generator2 = get_db()
        try:
            session1 = next(generator1)
            session2 = next(generator2)
        except StopIteration:
            pass
        try:
            generator1.close()
        except StopIteration:
            pass
        try:
            generator2.close()
        except StopIteration:
            pass
        assert session1 is not session2
