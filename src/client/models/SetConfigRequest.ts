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

import { exists, mapValues } from '../runtime';
import type { Value } from './Value';
import { ValueFromJSON, ValueFromJSONTyped, ValueToJSON } from './Value';

/**
 * Set config request model.
 * @export
 * @interface SetConfigRequest
 */
export interface SetConfigRequest {
    /**
     *
     * @type {Value}
     * @memberof SetConfigRequest
     */
    value: Value | null;
}

/**
 * Check if a given object implements the SetConfigRequest interface.
 */
export function instanceOfSetConfigRequest(value: object): boolean {
    let isInstance = true;
    isInstance = isInstance && 'value' in value;

    return isInstance;
}

export function SetConfigRequestFromJSON(json: any): SetConfigRequest {
    return SetConfigRequestFromJSONTyped(json, false);
}

export function SetConfigRequestFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean
): SetConfigRequest {
    if (json === undefined || json === null) {
        return json;
    }
    return {
        value: ValueFromJSON(json['value']),
    };
}

export function SetConfigRequestToJSON(value?: SetConfigRequest | null): any {
    if (value === undefined) {
        return undefined;
    }
    if (value === null) {
        return null;
    }
    return {
        value: ValueToJSON(value.value),
    };
}
