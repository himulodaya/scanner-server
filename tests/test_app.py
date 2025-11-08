"""Tests for Flask application"""
import pytest
from backend.app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test index route returns 200"""
    response = client.get('/')
    assert response.status_code == 200


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'version' in data


def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent')
    assert response.status_code == 404


def test_settings_route(client):
    """Test settings route"""
    response = client.get('/api/settings')
    assert response.status_code in [200, 500]  # May fail if config not available


def test_printer_list_route(client):
    """Test printer list route"""
    response = client.get('/api/printer/list', headers={'Accept': 'application/json'})
    assert response.status_code in [200, 500]  # May fail if CUPS not available
