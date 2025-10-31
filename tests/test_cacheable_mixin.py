"""
Tests pour le module cacheable_mixin.
"""

import tempfile
from typing import Any, Dict

import pytest

from src.core.cache_manager import CacheManager
from src.core.cacheable_mixin import CacheableMixin


class DummyAnalyzer(CacheableMixin):
    """Analyseur de test qui utilise le CacheableMixin."""

    def __init__(self, value: int = 0):
        super().__init__()
        self.value = value
        self.call_count = 0

    def expensive_operation(self) -> int:
        """Opération coûteuse simulée."""
        self.call_count += 1
        return self.value * 2

    def operation_with_params(self, multiplier: int) -> int:
        """Opération avec paramètres."""
        self.call_count += 1
        return self.value * multiplier

    def _get_default_cache_params(self) -> Dict[str, Any]:
        """Paramètres par défaut pour le cache."""
        return {"value": self.value}


class TestCacheableMixin:
    """Tests pour la classe CacheableMixin."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def analyzer(self, temp_cache_dir):
        """Crée un analyseur de test."""
        # Créer un gestionnaire de cache temporaire
        cache_manager = CacheManager(base_cache_dir=temp_cache_dir)
        
        # Créer l'analyseur
        analyzer = DummyAnalyzer(value=10)
        analyzer._cache_manager = cache_manager
        
        return analyzer

    def test_init_sets_attributes(self, analyzer):
        """Test que __init__ initialise correctement les attributs."""
        assert hasattr(analyzer, "_cache_manager")
        assert hasattr(analyzer, "_cache_enabled")
        assert hasattr(analyzer, "_analyzer_name")
        assert analyzer._cache_enabled is True
        assert analyzer._analyzer_name == "dummy"

    def test_enable_cache_true(self, analyzer):
        """Test d'activation du cache."""
        analyzer._cache_enabled = False
        analyzer.enable_cache(True)
        assert analyzer._cache_enabled is True

    def test_enable_cache_false(self, analyzer):
        """Test de désactivation du cache."""
        analyzer._cache_enabled = True
        analyzer.enable_cache(False)
        assert analyzer._cache_enabled is False

    def test_enable_cache_initializes_attributes(self):
        """Test que enable_cache initialise les attributs manquants."""
        # Créer un analyseur sans initialisation complète
        analyzer = object.__new__(DummyAnalyzer)
        analyzer.value = 5
        
        # enable_cache doit initialiser les attributs
        analyzer.enable_cache(True)
        
        assert hasattr(analyzer, "_cache_manager")
        assert hasattr(analyzer, "_analyzer_name")
        assert analyzer._cache_enabled is True

    def test_cached_operation_with_cache_hit(self, analyzer):
        """Test de cached_operation avec cache hit."""
        # Premier appel : calcul et mise en cache
        result1 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        assert result1 == 20
        assert analyzer.call_count == 1
        
        # Deuxième appel : depuis le cache
        result2 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        assert result2 == 20
        assert analyzer.call_count == 1  # Pas d'appel supplémentaire

    def test_cached_operation_with_cache_miss(self, analyzer):
        """Test de cached_operation avec cache miss."""
        # Deux appels avec des paramètres différents
        result1 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        result2 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 20}  # Paramètres différents
        )
        
        assert result1 == 20
        assert result2 == 20
        assert analyzer.call_count == 2  # Deux appels

    def test_cached_operation_with_cache_disabled(self, analyzer):
        """Test de cached_operation avec cache désactivé."""
        analyzer.enable_cache(False)
        
        # Deux appels identiques
        result1 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        result2 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        assert result1 == 20
        assert result2 == 20
        assert analyzer.call_count == 2  # Deux appels, pas de cache

    def test_cached_operation_without_cache_params(self, analyzer):
        """Test de cached_operation sans paramètres de cache explicites."""
        # Utilise _get_default_cache_params()
        result = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation
        )
        
        assert result == 20
        assert analyzer.call_count == 1

    def test_cached_operation_uses_default_params(self, analyzer):
        """Test que cached_operation utilise les paramètres par défaut."""
        # Premier appel sans paramètres
        result1 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation
        )
        
        # Deuxième appel sans paramètres (devrait utiliser le cache)
        result2 = analyzer.cached_operation(
            operation_name="test_op",
            operation_func=analyzer.expensive_operation
        )
        
        assert result1 == 20
        assert result2 == 20
        assert analyzer.call_count == 1  # Cache hit

    def test_cached_operation_different_operations(self, analyzer):
        """Test que différentes opérations ont des caches séparés."""
        result1 = analyzer.cached_operation(
            operation_name="op1",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        result2 = analyzer.cached_operation(
            operation_name="op2",
            operation_func=analyzer.expensive_operation,
            cache_params={"value": 10}
        )
        
        assert result1 == 20
        assert result2 == 20
        assert analyzer.call_count == 2  # Deux opérations différentes

    def test_clear_cache_all_operations(self, analyzer):
        """Test de clear_cache pour toutes les opérations."""
        # Créer des caches pour plusieurs opérations
        analyzer.cached_operation("op1", analyzer.expensive_operation, {"id": 1})
        analyzer.cached_operation("op2", analyzer.expensive_operation, {"id": 2})
        
        # Nettoyer tout
        deleted = analyzer.clear_cache()
        
        assert deleted == 2

    def test_clear_cache_specific_operation(self, analyzer):
        """Test de clear_cache pour une opération spécifique."""
        # Créer des caches
        analyzer.cached_operation("op1", analyzer.expensive_operation, {"id": 1})
        analyzer.cached_operation("op2", analyzer.expensive_operation, {"id": 2})
        
        # Nettoyer op1 uniquement
        deleted = analyzer.clear_cache(operation="op1")
        
        assert deleted == 1
        
        # Vérifier que op1 est supprimé et op2 existe
        analyzer.call_count = 0
        analyzer.cached_operation("op1", analyzer.expensive_operation, {"id": 1})
        assert analyzer.call_count == 1  # Cache miss, recalculé
        
        analyzer.call_count = 0
        analyzer.cached_operation("op2", analyzer.expensive_operation, {"id": 2})
        assert analyzer.call_count == 0  # Cache hit

    def test_get_cache_info_empty(self, analyzer):
        """Test de get_cache_info sur un cache vide."""
        info = analyzer.get_cache_info()
        
        assert "operations" in info
        assert "files" in info
        assert "size_mb" in info
        assert info["files"] == 0
        assert info["size_mb"] == 0.0

    def test_get_cache_info_with_data(self, analyzer):
        """Test de get_cache_info avec des données."""
        # Créer des caches
        analyzer.cached_operation("op1", analyzer.expensive_operation, {"id": 1})
        analyzer.cached_operation("op2", analyzer.expensive_operation, {"id": 2})
        
        info = analyzer.get_cache_info()
        
        assert info["files"] == 2
        assert info["size_mb"] >= 0  # Peut être 0.0 si les fichiers sont très petits
        assert "op1" in info["operations"]
        assert "op2" in info["operations"]

    def test_get_default_cache_params(self, analyzer):
        """Test de _get_default_cache_params."""
        params = analyzer._get_default_cache_params()
        
        assert params == {"value": 10}

    def test_cached_operation_with_lambda(self, analyzer):
        """Test de cached_operation avec une fonction lambda."""
        result = analyzer.cached_operation(
            operation_name="lambda_op",
            operation_func=lambda: analyzer.value * 3,
            cache_params={"multiplier": 3}
        )
        
        assert result == 30

    def test_cached_operation_preserves_return_types(self, analyzer):
        """Test que cached_operation préserve les types de retour."""
        # Liste
        list_result = analyzer.cached_operation(
            "list_op",
            lambda: [1, 2, 3],
            {"type": "list"}
        )
        assert isinstance(list_result, list)
        assert list_result == [1, 2, 3]
        
        # Dict
        dict_result = analyzer.cached_operation(
            "dict_op",
            lambda: {"key": "value"},
            {"type": "dict"}
        )
        assert isinstance(dict_result, dict)
        assert dict_result == {"key": "value"}
        
        # String
        str_result = analyzer.cached_operation(
            "str_op",
            lambda: "test",
            {"type": "str"}
        )
        assert isinstance(str_result, str)
        assert str_result == "test"


class TestCacheableMixinWithMultipleAnalyzers:
    """Tests avec plusieurs analyseurs utilisant CacheableMixin."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_multiple_analyzers_separate_caches(self, temp_cache_dir):
        """Test que plusieurs analyseurs ont des caches séparés."""
        cache_manager = CacheManager(base_cache_dir=temp_cache_dir)
        
        analyzer1 = DummyAnalyzer(value=10)
        analyzer1._cache_manager = cache_manager
        
        analyzer2 = DummyAnalyzer(value=20)
        analyzer2._cache_manager = cache_manager
        
        # Créer des caches avec des paramètres différents pour éviter collision
        result1 = analyzer1.cached_operation("op", analyzer1.expensive_operation, {"value": 10})
        result2 = analyzer2.cached_operation("op", analyzer2.expensive_operation, {"value": 20})
        
        assert result1 == 20  # 10 * 2
        assert result2 == 40  # 20 * 2
        assert analyzer1.call_count == 1
        assert analyzer2.call_count == 1
        
        # Les caches sont séparés
        info = cache_manager.get_info()
        assert "dummy" in info["analyzers"]
        assert info["analyzers"]["dummy"]["files"] == 2
