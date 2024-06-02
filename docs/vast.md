# Vast.Ai Integration

Currently, Distributaur supports Vast.ai as a compute provider. Vast.ai is a decentralized cloud provider that allows users to rent out GPU instances for a variety of tasks. Distributaur provides a simple interface to interact with Vast.ai's API to create, manage, and destroy instances.

This guide provides an overview of the Vast.ai integration module in the Distributaur package, which handles interaction with the Vast.ai API for managing and renting virtual machine instances.

## HTTP Utilities

### `http_get(url, headers)`

This function sends a GET request to the specified URL with the provided headers. It returns the parsed JSON response if successful and raises a `RequestException` if an error occurs during the request. Detailed error information is printed for better debugging.

### `apiurl(subpath: str, query_args: Dict = None, api_key: str = None) -> str`

This function constructs a full API URL by combining a base URL, subpath, optional query arguments, and an optional API key. The resulting URL can be used to make API requests to the Vast.ai service.

### `http_put(req_url, headers, json)`

This function sends a PUT request to the specified URL with the provided headers and JSON payload. It returns the response object if the request is successful and raises an exception if there's an issue with the request.

### `http_del(req_url, headers, json={})`

This function sends a DELETE request to the specified URL with the provided headers and optional JSON payload. It returns the response object if the request is successful and raises an exception if there's an issue with the request.

### `http_post(req_url, headers, json={})`

This function sends a POST request to the specified URL with the provided headers and optional JSON payload. It attempts to handle any exceptions that occur and prints detailed error responses for better debugging. The response object is returned if the request is successful.

## Query Parsing

### `parse_query(query_str: str, res: Dict = None, fields={}, field_alias={}, field_multiplier={}) -> Dict`

This function parses a string query into a structured dictionary using specified fields, aliases, and multipliers. It supports various comparison operators and complex queries. The function validates the query syntax and raises a `ValueError` if there are any syntax errors or invalid field/value combinations.

## Runtype and Environment Parsing

### `get_runtype(args)`

This function determines the runtype based on the provided command-line arguments. It handles different combinations of arguments such as `--jupyter`, `--ssh`, and `--direct` to determine the appropriate runtype for the instance.

### `parse_env(envs)`

This function parses environment variables from a string and returns a dictionary containing the parsed key-value pairs. It supports different formats for specifying environment variables and handles parsing of port mappings and key-value pairs.

## Offer Search and Instance Management

### `search_offers(max_price)`

This function searches for offers below a specified maximum price using the Vast.ai API. It constructs the search URL based on the provided criteria and handles the API request. If successful, it returns a list of offers that match the criteria. If an error occurs during the request, it raises a `RequestException`.

### `create_instance(offer_id, image, env)`

This function creates a virtual machine instance using the specified offer ID, image, and environment settings. It prepares the necessary payload for the instance creation API call and sends the request. If the instance is successfully created, it returns a dictionary containing the details of the new instance. If there are any missing or invalid environment settings, it raises a `ValueError`. If the instance creation fails, it raises an `Exception` with the error message.

### `destroy_instance(instance_id)`

This function destroys a virtual machine instance specified by its ID. It sends a DELETE request to the Vast.ai API to terminate the instance and returns the server response as a dictionary.

## Node Rental and Termination

### `rent_nodes(max_price, max_nodes, image, api_key, env=get_env_vars(".env"))`

This function searches for and rents nodes based on specified criteria such as maximum price per hour, maximum number of nodes, and image. It iterates over the available offers and attempts to create instances for each offer until the desired number of nodes is reached. If an offer is unavailable or an error occurs during the renting process, it skips to the next offer. The function returns a list of dictionaries, each containing the details of a rented node, including the offer ID and instance ID.

### `terminate_nodes(nodes)`

This function terminates a list of nodes by sending a termination request for each node's instance ID. It ensures that all specified nodes are properly shut down. If an error occurs during the termination of any node, it prints an error message.

::: distributaur.vast
    :docstring:
    :members:
    :undoc-members:
    :show-inheritance: