import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from job.state_machine import JobStateMachine, InvalidTransition

def test_valid_transitions():
    sm = JobStateMachine()
    assert sm.can_transition('pending', 'running') is True
    assert sm.can_transition('running', 'done') is True
    assert sm.can_transition('running', 'failed') is True
    assert sm.can_transition('running', 'cancelled') is True
    assert sm.can_transition('failed', 'pending') is True

def test_invalid_transitions():
    sm = JobStateMachine()
    assert sm.can_transition('done', 'running') is False
    assert sm.can_transition('done', 'pending') is False
    assert sm.can_transition('cancelled', 'running') is False
    assert sm.can_transition('pending', 'done') is False

def test_transition_updates_status():
    sm = JobStateMachine()
    new_status = sm.transition('pending', 'running')
    assert new_status == 'running'

def test_invalid_transition_raises():
    sm = JobStateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition('done', 'running')

def test_retry_limit():
    sm = JobStateMachine(max_retries=3)
    assert sm.can_retry(retry_count=2) is True
    assert sm.can_retry(retry_count=3) is False
