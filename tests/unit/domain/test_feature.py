"""Testes unitários para entidade Feature."""
import pytest

from backlog_manager.domain.entities.feature import Feature


class TestFeature:
    """Testes para entidade Feature."""

    def test_create_valid_feature(self) -> None:
        """Deve criar feature com dados válidos."""
        feature = Feature(id="feature_001", name="MVP Core", wave=1)

        assert feature.id == "feature_001"
        assert feature.name == "MVP Core"
        assert feature.wave == 1

    def test_reject_empty_id(self) -> None:
        """Deve rejeitar ID vazio."""
        with pytest.raises(ValueError, match="ID da feature não pode ser vazio"):
            Feature(id="", name="MVP", wave=1)

    def test_reject_whitespace_id(self) -> None:
        """Deve rejeitar ID com apenas espaços."""
        with pytest.raises(ValueError, match="ID da feature não pode ser vazio"):
            Feature(id="   ", name="MVP", wave=1)

    def test_reject_empty_name(self) -> None:
        """Deve rejeitar nome vazio."""
        with pytest.raises(ValueError, match="Nome da feature não pode ser vazio"):
            Feature(id="feature_001", name="", wave=1)

    def test_reject_whitespace_name(self) -> None:
        """Deve rejeitar nome com apenas espaços."""
        with pytest.raises(ValueError, match="Nome da feature não pode ser vazio"):
            Feature(id="feature_001", name="   ", wave=1)

    def test_reject_wave_zero(self) -> None:
        """Deve rejeitar onda igual a zero."""
        with pytest.raises(ValueError, match="Onda deve ser um número positivo"):
            Feature(id="feature_001", name="MVP", wave=0)

    def test_reject_negative_wave(self) -> None:
        """Deve rejeitar onda negativa."""
        with pytest.raises(ValueError, match="Onda deve ser um número positivo"):
            Feature(id="feature_001", name="MVP", wave=-1)

    def test_accept_large_wave_numbers(self) -> None:
        """Deve aceitar números de onda grandes (gaps permitidos)."""
        feature = Feature(id="feature_001", name="Futuro Distante", wave=9999)
        assert feature.wave == 9999

    def test_feature_equality_by_id(self) -> None:
        """Features são iguais se têm mesmo ID."""
        feature1 = Feature(id="feature_001", name="MVP", wave=1)
        feature2 = Feature(id="feature_001", name="Outro Nome", wave=2)
        feature3 = Feature(id="feature_002", name="MVP", wave=1)

        assert feature1 == feature2  # Mesmo ID
        assert feature1 != feature3  # IDs diferentes

    def test_feature_hashable(self) -> None:
        """Features devem ser hashable."""
        feature1 = Feature(id="feature_001", name="MVP", wave=1)
        feature2 = Feature(id="feature_001", name="Outro Nome", wave=2)
        feature3 = Feature(id="feature_002", name="MVP", wave=1)

        features_set = {feature1, feature2, feature3}
        assert len(features_set) == 2  # feature1 e feature2 são iguais

    def test_feature_with_non_sequential_waves(self) -> None:
        """Deve permitir ondas não sequenciais (gaps)."""
        feature1 = Feature(id="feature_001", name="Onda 1", wave=1)
        feature2 = Feature(id="feature_002", name="Onda 10", wave=10)
        feature3 = Feature(id="feature_003", name="Onda 100", wave=100)

        assert feature1.wave == 1
        assert feature2.wave == 10
        assert feature3.wave == 100
