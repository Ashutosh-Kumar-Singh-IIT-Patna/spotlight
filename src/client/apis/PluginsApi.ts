/* tslint:disable */
/* eslint-disable */
/**
 * FastAPI
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.1.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from '../runtime';
import type { HTTPValidationError } from '../models';
import { HTTPValidationErrorFromJSON, HTTPValidationErrorToJSON } from '../models';

export interface GetEntrypointRequest {
    name: any;
}

/**
 *
 */
export class PluginsApi extends runtime.BaseAPI {
    /**
     * Get the frontend entrypoint for a plugin
     *
     */
    async getEntrypointRaw(
        requestParameters: GetEntrypointRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction
    ): Promise<runtime.ApiResponse<any>> {
        if (requestParameters.name === null || requestParameters.name === undefined) {
            throw new runtime.RequiredError(
                'name',
                'Required parameter requestParameters.name was null or undefined when calling getEntrypoint.'
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request(
            {
                path: `/api/plugins/{name}/main.js`.replace(
                    `{${'name'}}`,
                    encodeURIComponent(String(requestParameters.name))
                ),
                method: 'GET',
                headers: headerParameters,
                query: queryParameters,
            },
            initOverrides
        );

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Get the frontend entrypoint for a plugin
     *
     */
    async getEntrypoint(
        requestParameters: GetEntrypointRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction
    ): Promise<any> {
        const response = await this.getEntrypointRaw(requestParameters, initOverrides);
        return await response.value();
    }

    /**
     * Get a list of all the installed spotlight plugins
     *
     */
    async getPluginsRaw(
        initOverrides?: RequestInit | runtime.InitOverrideFunction
    ): Promise<runtime.ApiResponse<any>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request(
            {
                path: `/api/plugins/`,
                method: 'GET',
                headers: headerParameters,
                query: queryParameters,
            },
            initOverrides
        );

        if (this.isJsonMime(response.headers.get('content-type'))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Get a list of all the installed spotlight plugins
     *
     */
    async getPlugins(
        initOverrides?: RequestInit | runtime.InitOverrideFunction
    ): Promise<any> {
        const response = await this.getPluginsRaw(initOverrides);
        return await response.value();
    }
}
