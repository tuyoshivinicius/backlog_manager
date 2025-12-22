"""Testes unitários para DeveloperLoadBalancer."""
from backlog_manager.domain.entities.developer import Developer
from backlog_manager.domain.entities.story import Story
from backlog_manager.domain.services.developer_load_balancer import DeveloperLoadBalancer
from backlog_manager.domain.value_objects.story_point import StoryPoint


class TestDeveloperLoadBalancer:
    """Testes para balanceamento de carga de desenvolvedores."""

    def test_sort_by_load_random_tiebreak_deterministic(self) -> None:
        """Deve ordenar por carga e desempatar aleatoriamente com seed fixa."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        dev2 = Developer(id="D2", name="Bruno")
        dev3 = Developer(id="D3", name="Carlos")

        # D1 tem 2 histórias, D2 e D3 têm 1 cada
        stories = [
            Story(
                id="S1",
                feature="Login",
                name="Story 1",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S2",
                feature="Login",
                name="Story 2",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S3",
                feature="Login",
                name="Story 3",
                story_point=StoryPoint(5),
                developer_id="D2",
            ),
            Story(
                id="S4",
                feature="Login",
                name="Story 4",
                story_point=StoryPoint(5),
                developer_id="D3",
            ),
        ]

        # Act - Com seed fixa, resultado é determinístico
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
            [dev1, dev2, dev3], stories, random_seed=42
        )

        # Assert
        assert len(sorted_devs) == 3
        # D2 e D3 vêm antes (1 história cada), D1 por último (2 histórias)
        assert sorted_devs[0].id in ["D2", "D3"]
        assert sorted_devs[1].id in ["D2", "D3"]
        assert sorted_devs[2].id == "D1"
        # Os dois primeiros devs não podem ser iguais
        assert sorted_devs[0].id != sorted_devs[1].id

    def test_sort_by_load_random_tiebreak_different_seeds(self) -> None:
        """Deve produzir diferentes ordens com diferentes seeds."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        dev2 = Developer(id="D2", name="Bruno")
        dev3 = Developer(id="D3", name="Carlos")

        # Todos com carga 0
        stories = []

        # Act - Executar com 3 seeds diferentes
        results = []
        for seed in [10, 20, 30]:
            sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
                [dev1, dev2, dev3], stories, random_seed=seed
            )
            # Capturar ordem dos IDs
            order = tuple(dev.id for dev in sorted_devs)
            results.append(order)

        # Assert - Com seeds diferentes, deve haver pelo menos 2 ordens diferentes
        # (estatisticamente improvável que 3 shuffles dêem sempre o mesmo resultado)
        assert len(set(results)) >= 2, "Deve haver variação com diferentes seeds"

    def test_sort_by_load_random_tiebreak_single_dev(self) -> None:
        """Deve funcionar com apenas 1 desenvolvedor."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        stories = [
            Story(
                id="S1",
                feature="Login",
                name="Story 1",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
        ]

        # Act
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak([dev1], stories)

        # Assert
        assert len(sorted_devs) == 1
        assert sorted_devs[0].id == "D1"

    def test_sort_by_load_random_tiebreak_no_stories(self) -> None:
        """Deve funcionar quando todos desenvolvedores têm carga 0."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        dev2 = Developer(id="D2", name="Bruno")
        dev3 = Developer(id="D3", name="Carlos")

        stories = []  # Nenhuma história alocada

        # Act - Com seed fixa para reprodutibilidade
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
            [dev1, dev2, dev3], stories, random_seed=42
        )

        # Assert
        assert len(sorted_devs) == 3
        # Todos os 3 devs devem estar na lista
        ids = {dev.id for dev in sorted_devs}
        assert ids == {"D1", "D2", "D3"}

    def test_sort_by_load_random_tiebreak_different_loads(self) -> None:
        """Deve ordenar por carga quando as cargas são diferentes."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        dev2 = Developer(id="D2", name="Bruno")
        dev3 = Developer(id="D3", name="Carlos")

        # D1: 3 histórias, D2: 2 histórias, D3: 1 história
        stories = [
            Story(
                id="S1",
                feature="Login",
                name="Story 1",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S2",
                feature="Login",
                name="Story 2",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S3",
                feature="Login",
                name="Story 3",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S4",
                feature="Login",
                name="Story 4",
                story_point=StoryPoint(5),
                developer_id="D2",
            ),
            Story(
                id="S5",
                feature="Login",
                name="Story 5",
                story_point=StoryPoint(5),
                developer_id="D2",
            ),
            Story(
                id="S6",
                feature="Login",
                name="Story 6",
                story_point=StoryPoint(5),
                developer_id="D3",
            ),
        ]

        # Act
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
            [dev1, dev2, dev3], stories
        )

        # Assert - Ordem deve ser: D3 (1), D2 (2), D1 (3)
        assert len(sorted_devs) == 3
        assert sorted_devs[0].id == "D3"  # Menor carga
        assert sorted_devs[1].id == "D2"
        assert sorted_devs[2].id == "D1"  # Maior carga

    def test_sort_by_load_random_tiebreak_mixed_loads(self) -> None:
        """Deve ordenar por carga e embaralhar apenas devs com mesma carga."""
        # Arrange
        dev1 = Developer(id="D1", name="Ana")
        dev2 = Developer(id="D2", name="Bruno")
        dev3 = Developer(id="D3", name="Carlos")
        dev4 = Developer(id="D4", name="Diana")

        # D1: 2, D2: 1, D3: 1, D4: 3
        stories = [
            Story(
                id="S1",
                feature="Login",
                name="Story 1",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S2",
                feature="Login",
                name="Story 2",
                story_point=StoryPoint(5),
                developer_id="D1",
            ),
            Story(
                id="S3",
                feature="Login",
                name="Story 3",
                story_point=StoryPoint(5),
                developer_id="D2",
            ),
            Story(
                id="S4",
                feature="Login",
                name="Story 4",
                story_point=StoryPoint(5),
                developer_id="D3",
            ),
            Story(
                id="S5",
                feature="Login",
                name="Story 5",
                story_point=StoryPoint(5),
                developer_id="D4",
            ),
            Story(
                id="S6",
                feature="Login",
                name="Story 6",
                story_point=StoryPoint(5),
                developer_id="D4",
            ),
            Story(
                id="S7",
                feature="Login",
                name="Story 7",
                story_point=StoryPoint(5),
                developer_id="D4",
            ),
        ]

        # Act - Com seed fixa
        sorted_devs = DeveloperLoadBalancer.sort_by_load_random_tiebreak(
            [dev1, dev2, dev3, dev4], stories, random_seed=42
        )

        # Assert
        assert len(sorted_devs) == 4
        # Primeiros 2: D2 e D3 (carga 1) em qualquer ordem
        assert sorted_devs[0].id in ["D2", "D3"]
        assert sorted_devs[1].id in ["D2", "D3"]
        assert sorted_devs[0].id != sorted_devs[1].id
        # Terceiro: D1 (carga 2)
        assert sorted_devs[2].id == "D1"
        # Último: D4 (carga 3)
        assert sorted_devs[3].id == "D4"
