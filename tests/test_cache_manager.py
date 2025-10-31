"""
Tests pour le module cache_manager.
"""

import pickle
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.core.cache_manager import CacheManager, get_cache_manager


class TestCacheManager:
    """Tests pour la classe CacheManager."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Crée une instance de CacheManager pour les tests."""
        return CacheManager(base_cache_dir=temp_cache_dir)

    def test_init_creates_cache_directory(self, temp_cache_dir):
        """Test que l'initialisation crée le répertoire de cache."""
        cache_dir = Path(temp_cache_dir) / "test_cache"
        manager = CacheManager(base_cache_dir=str(cache_dir))
        
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_generate_key_consistent(self, cache_manager):
        """Test que _generate_key produit des clés cohérentes."""
        params1 = {"threshold": 10, "method": "iqr"}
        params2 = {"method": "iqr", "threshold": 10}  # Ordre différent
        
        key1 = cache_manager._generate_key("interactions", "aggregate", params1)
        key2 = cache_manager._generate_key("interactions", "aggregate", params2)
        
        # Les clés doivent être identiques malgré l'ordre différent
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length

    def test_generate_key_different_params(self, cache_manager):
        """Test que _generate_key produit des clés différentes pour des paramètres différents."""
        params1 = {"threshold": 10}
        params2 = {"threshold": 20}
        
        key1 = cache_manager._generate_key("interactions", "aggregate", params1)
        key2 = cache_manager._generate_key("interactions", "aggregate", params2)
        
        assert key1 != key2

    def test_get_cache_path_creates_structure(self, cache_manager):
        """Test que _get_cache_path crée la structure de répertoires."""
        cache_key = "test_key_123"
        path = cache_manager._get_cache_path("test_analyzer", "test_operation", cache_key)
        
        assert path.parent.exists()
        assert "test_analyzer" in str(path)
        assert "test_operation" in str(path)
        assert path.name == f"{cache_key}.pkl"

    def test_set_and_get_success(self, cache_manager):
        """Test de sauvegarde et récupération réussies."""
        test_data = {"result": [1, 2, 3], "metadata": "test"}
        params = {"param1": "value1"}
        
        # Sauvegarder
        success = cache_manager.set("test_analyzer", "test_op", params, test_data)
        assert success is True
        
        # Récupérer
        retrieved = cache_manager.get("test_analyzer", "test_op", params)
        assert retrieved == test_data

    def test_get_cache_miss(self, cache_manager):
        """Test de récupération avec cache miss."""
        params = {"nonexistent": "params"}
        result = cache_manager.get("test_analyzer", "test_op", params)
        
        assert result is None

    def test_set_with_different_data_types(self, cache_manager):
        """Test de sauvegarde avec différents types de données."""
        test_cases = [
            {"data": [1, 2, 3], "params": {"type": "list"}},
            {"data": {"key": "value"}, "params": {"type": "dict"}},
            {"data": "string_data", "params": {"type": "str"}},
            {"data": 42, "params": {"type": "int"}},
            {"data": {"nested": {"deep": "value"}}, "params": {"type": "nested"}},
        ]
        
        for test_case in test_cases:
            success = cache_manager.set(
                "test_analyzer",
                "test_op",
                test_case["params"],
                test_case["data"]
            )
            assert success is True
            
            retrieved = cache_manager.get("test_analyzer", "test_op", test_case["params"])
            assert retrieved == test_case["data"]

    def test_set_creates_metadata(self, cache_manager, temp_cache_dir):
        """Test que set() sauvegarde les métadonnées correctement."""
        test_data = {"test": "data"}
        params = {"param": "value"}
        
        cache_manager.set("test_analyzer", "test_op", params, test_data)
        
        # Récupérer directement depuis le fichier pickle
        cache_key = cache_manager._generate_key("test_analyzer", "test_op", params)
        cache_path = cache_manager._get_cache_path("test_analyzer", "test_op", cache_key)
        
        with open(cache_path, "rb") as f:
            cached_data = pickle.load(f)
        
        assert "data" in cached_data
        assert "timestamp" in cached_data
        assert "analyzer" in cached_data
        assert "operation" in cached_data
        assert "params" in cached_data
        
        assert cached_data["data"] == test_data
        assert cached_data["analyzer"] == "test_analyzer"
        assert cached_data["operation"] == "test_op"
        assert cached_data["params"] == params

    def test_clear_all_cache(self, cache_manager):
        """Test de nettoyage complet du cache."""
        # Créer plusieurs entrées
        for i in range(3):
            cache_manager.set(f"analyzer_{i}", "operation", {"id": i}, f"data_{i}")
        
        # Nettoyer tout
        deleted = cache_manager.clear()
        
        assert deleted == 3
        
        # Vérifier que tout est supprimé
        for i in range(3):
            result = cache_manager.get(f"analyzer_{i}", "operation", {"id": i})
            assert result is None

    def test_clear_specific_analyzer(self, cache_manager):
        """Test de nettoyage d'un analyseur spécifique."""
        # Créer des entrées pour différents analyseurs
        cache_manager.set("analyzer1", "op1", {"id": 1}, "data1")
        cache_manager.set("analyzer1", "op2", {"id": 2}, "data2")
        cache_manager.set("analyzer2", "op1", {"id": 3}, "data3")
        
        # Nettoyer analyzer1 uniquement
        deleted = cache_manager.clear(analyzer_name="analyzer1")
        
        assert deleted == 2
        
        # Vérifier que analyzer1 est supprimé
        assert cache_manager.get("analyzer1", "op1", {"id": 1}) is None
        assert cache_manager.get("analyzer1", "op2", {"id": 2}) is None
        
        # Vérifier que analyzer2 existe toujours
        assert cache_manager.get("analyzer2", "op1", {"id": 3}) == "data3"

    def test_clear_specific_operation(self, cache_manager):
        """Test de nettoyage d'une opération spécifique."""
        # Créer des entrées pour différentes opérations
        cache_manager.set("analyzer1", "op1", {"id": 1}, "data1")
        cache_manager.set("analyzer1", "op2", {"id": 2}, "data2")
        
        # Nettoyer op1 uniquement
        deleted = cache_manager.clear(analyzer_name="analyzer1", operation="op1")
        
        assert deleted == 1
        
        # Vérifier que op1 est supprimé
        assert cache_manager.get("analyzer1", "op1", {"id": 1}) is None
        
        # Vérifier que op2 existe toujours
        assert cache_manager.get("analyzer1", "op2", {"id": 2}) == "data2"

    def test_get_info_empty_cache(self, cache_manager):
        """Test de get_info sur un cache vide."""
        info = cache_manager.get_info()
        
        assert "base_directory" in info
        assert info["total_files"] == 0
        assert info["total_size_mb"] == 0.0
        assert info["analyzers"] == {}

    def test_get_info_with_data(self, cache_manager):
        """Test de get_info avec des données."""
        # Créer des entrées
        cache_manager.set("analyzer1", "op1", {"id": 1}, "data" * 1000)
        cache_manager.set("analyzer1", "op2", {"id": 2}, "data" * 2000)
        cache_manager.set("analyzer2", "op1", {"id": 3}, "data" * 3000)
        
        info = cache_manager.get_info()
        
        assert info["total_files"] == 3
        assert info["total_size_mb"] > 0
        assert "analyzer1" in info["analyzers"]
        assert "analyzer2" in info["analyzers"]
        
        # Vérifier analyzer1
        assert info["analyzers"]["analyzer1"]["files"] == 2
        assert "op1" in info["analyzers"]["analyzer1"]["operations"]
        assert "op2" in info["analyzers"]["analyzer1"]["operations"]
        
        # Vérifier analyzer2
        assert info["analyzers"]["analyzer2"]["files"] == 1
        assert "op1" in info["analyzers"]["analyzer2"]["operations"]

    def test_get_with_invalid_cache_format(self, cache_manager, temp_cache_dir):
        """Test de get() avec un format de cache invalide."""
        params = {"test": "params"}
        cache_key = cache_manager._generate_key("test_analyzer", "test_op", params)
        cache_path = cache_manager._get_cache_path("test_analyzer", "test_op", cache_key)
        
        # Créer un cache avec un format invalide
        with open(cache_path, "wb") as f:
            pickle.dump({"invalid": "format"}, f)
        
        result = cache_manager.get("test_analyzer", "test_op", params)
        assert result is None

    def test_get_with_corrupted_cache(self, cache_manager, temp_cache_dir):
        """Test de get() avec un cache corrompu."""
        params = {"test": "params"}
        cache_key = cache_manager._generate_key("test_analyzer", "test_op", params)
        cache_path = cache_manager._get_cache_path("test_analyzer", "test_op", cache_key)
        
        # Créer un fichier corrompu
        with open(cache_path, "wb") as f:
            f.write(b"corrupted data")
        
        result = cache_manager.get("test_analyzer", "test_op", params)
        assert result is None

    def test_set_with_unserializable_data(self, cache_manager):
        """Test de set() avec des données non sérialisables."""
        # Les lambdas ne sont pas sérialisables par pickle
        test_data = lambda x: x * 2
        params = {"test": "params"}
        
        success = cache_manager.set("test_analyzer", "test_op", params, test_data)
        assert success is False


class TestGetCacheManager:
    """Tests pour la fonction get_cache_manager()."""

    def test_get_cache_manager_singleton(self):
        """Test que get_cache_manager() retourne toujours la même instance."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        assert manager1 is manager2

    def test_get_cache_manager_returns_cache_manager(self):
        """Test que get_cache_manager() retourne bien un CacheManager."""
        manager = get_cache_manager()
        assert isinstance(manager, CacheManager)
