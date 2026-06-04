from dependency_injector import containers, providers
from user.infra.repositor.user_repo import UserRepository

class container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["user"]
    )

    user_repo = providers.Factory(UserRepository)