# -*- coding:utf-8 -*-
import ast
import logging

from django.db.transaction import commit_on_success

from networkapi.api_rest import exceptions as api_exceptions
from networkapi.api_vip_request import exceptions, facade
from networkapi.api_vip_request.permissions import DeployCreate, DeployDelete, DeployUpdate, Read, Write
from networkapi.api_vip_request.serializers import VipRequestSerializer
from networkapi.settings import SPECS
from networkapi.util import logs_method_apiview, permission_classes_apiview
from networkapi.util.json_validate import json_validate, raise_json_validate

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


log = logging.getLogger(__name__)


class VipRequestDeployView(APIView):

    @permission_classes_apiview((IsAuthenticated, Write, DeployCreate))
    @logs_method_apiview
    def post(self, request, *args, **kwargs):
        """Create vip request by list"""

        vip_request_ids = kwargs['vip_request_ids'].split(';')
        vips = facade.get_vip_request(vip_request_ids)
        vip_serializer = VipRequestSerializer(vips, many=True)
        locks_list = facade.create_lock(vip_serializer.data)
        try:
            response = facade.create_real_vip_request(vip_serializer.data)
        except Exception, exception:
            log.error(exception)
            raise api_exceptions.NetworkAPIException(exception)
        finally:
            facade.destroy_lock(locks_list)

        return Response(response)

    @permission_classes_apiview((IsAuthenticated, Write, DeployDelete))
    @logs_method_apiview
    def delete(self, request, *args, **kwargs):
        """Delete vip request by list"""

        vip_request_ids = kwargs['vip_request_ids'].split(';')
        vips = facade.get_vip_request(vip_request_ids)
        vip_serializer = VipRequestSerializer(vips, many=True)
        locks_list = facade.create_lock(vip_serializer.data)
        try:
            response = facade.delete_real_vip_request(vip_serializer.data)
        except Exception, exception:
            log.error(exception)
            raise api_exceptions.NetworkAPIException(exception)
        finally:
            facade.destroy_lock(locks_list)

        return Response(response)

    @permission_classes_apiview((IsAuthenticated, Write, DeployUpdate))
    @logs_method_apiview
    def put(self, request, *args, **kwargs):
        """Update vip request by list"""

        return Response({})


class VipRequestDBView(APIView):

    @permission_classes_apiview((IsAuthenticated, Read))
    @logs_method_apiview
    def get(self, request, *args, **kwargs):
        """Method to return a vip request by id
        Param vip_request_id: vip request id
        """
        try:
            if not kwargs.get('vip_request_ids'):

                try:
                    search = ast.literal_eval(request.GET.get('search'))
                except:
                    search = {}

                vips_requests = facade.get_vip_request_by_search(search)

                serializer_vips = VipRequestSerializer(
                    vips_requests['vips'],
                    many=True
                )
                data = {
                    'vips': serializer_vips.data,
                    'total': vips_requests['total'],
                }

            else:
                vip_request_ids = kwargs['vip_request_ids'].split(';')

                vips_requests = facade.get_vip_request(vip_request_ids)

                if vips_requests:
                    serializer_vips = VipRequestSerializer(
                        vips_requests,
                        many=True
                    )
                    data = {
                        'vips': serializer_vips.data
                    }
                    log.info(serializer_vips.data)
                else:
                    raise exceptions.VipRequestDoesNotExistException()

            return Response(data, status.HTTP_200_OK)

        except Exception, exception:
            log.error(exception)
            raise api_exceptions.NetworkAPIException(exception)

    @permission_classes_apiview((IsAuthenticated, Write))
    @logs_method_apiview
    @raise_json_validate('vip_post')
    @commit_on_success
    def post(self, request, *args, **kwargs):
        """
        Method to save a vip request
        Param request.DATA: info of vip request in dict
        """

        data = request.DATA

        json_validate(SPECS.get('vip_post')).validate(data)

        response = list()
        for vip in data['vips']:
            vp = facade.create_vip_request(vip)
            response.append({'id': vp.id})

        return Response(response, status.HTTP_201_CREATED)

    @permission_classes_apiview((IsAuthenticated, Write))
    @logs_method_apiview
    @raise_json_validate('vip_put')
    @commit_on_success
    def put(self, request, *args, **kwargs):
        """
        Method to save a vip request
        Param request.DATA: info of vip request in dict
        """
        data = request.DATA

        json_validate(SPECS.get('vip_put')).validate(data)

        response = {}
        for vip in data['vips']:
            facade.update_vip_request(vip)

        return Response(response, status.HTTP_200_OK)

    @permission_classes_apiview((IsAuthenticated, Write))
    @commit_on_success
    def delete(self, request, *args, **kwargs):
        """
        Method to delete
        """
        vip_request_ids = kwargs['vip_request_ids'].split(';')
        response = {}
        facade.delete_vip_request(vip_request_ids)

        return Response(response)
