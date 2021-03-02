class BaseUpdaterException(Exception):
    pass


class ConfigPushError(BaseUpdaterException):
    pass


class DeploymentBaseFetchError(BaseUpdaterException):
    pass


class DeploymentBaseFormatError(BaseUpdaterException):
    def __init__(self, message):
        msg = f"Incorrect format of deploymentBaseRef. {message}"
        super().__init__(msg)


class FeedbackPushError(BaseUpdaterException):
    pass


