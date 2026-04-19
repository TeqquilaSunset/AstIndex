class UserService:
    def get_user(self):
        repo = ExternalRepository()  # noqa: F821
        data = repo.fetch_data()
        return data
