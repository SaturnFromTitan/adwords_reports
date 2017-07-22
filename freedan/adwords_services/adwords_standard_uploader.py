import suds

from freedan.adwords_services.adwords_error import AdWordsError
from freedan.other_services.error_retryer import ErrorRetryer

MAX_OPERATIONS_STANDARD_UPLOAD = 5000


class AdWordsStandardUploader:
    """ AdWords service object for standard uploads of operations to AdWords API """
    def __init__(self, adwords_service):
        """
        :param adwords_service: AdWords model
        """
        self.adwords_service = adwords_service
        self.client = adwords_service.client
        self.max_standard_upload = MAX_OPERATIONS_STANDARD_UPLOAD

    @ErrorRetryer()
    def upload(self, service_string, operations, debug, partial_failure, label):
        """ Uploads a list of operations to adwords api using standard mutate service.
        :param service_string: adwords service object associated with the operations
        :param operations: list of operations
        :param debug: bool
        :param partial_failure: bool
        :param label: bool
        :return: response from adwords
        """
        assert isinstance(operations, list)
        service = self.adwords_service.init_service(service_string)

        self.client.partial_failure = partial_failure
        self.client.validate_only = debug
        print("##### OperationUpload is LIVE: %s. #####" % (not self.client.validate_only))

        result = None
        try:
            if label:
                result = service.mutateLabel(operations)
            else:
                result = service.mutate(operations)

        except suds.WebFault as e:
            error_list = e.fault.detail.ApiExceptionFault.errors
            self.print_failures(error_list)
        finally:
            # reset validate only header
            self.client.validate_only = False

        if not debug and result is None:
            print("All operations successfully uploaded.")
        elif self.client.partial_failure and 'partialFailureErrors' in result:
            error_list = result['partialFailureErrors']
            self.print_failures(error_list)

        return result

    @staticmethod
    def print_failures(error_list):
        """ Printing failed operations + reason using AdWordsError model """
        error_texts = list()
        for adwords_error in error_list:
            index = adwords_error["fieldPathElements"][0]["index"]
            error = AdWordsError.from_adwords_error(index=index, adwords_error=adwords_error)
            error_texts.append(error.to_string())

        error_message = "\n".join(error_texts) or "All operations successfully uploaded."
        print(error_message)
