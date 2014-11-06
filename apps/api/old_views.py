
class CreateWorkoutView(APIView):
    """
    Creates a timing session, e.g., a workout or race.
    """
    permission_classes = ()

    def post(self, request):
        serializer = CreateTimingSessionSerializer(data=request.DATA)

        if not serializer.is_valid():
            return HttpResponse(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        data = serializer.data

        # Create the session in the database.
        session = TimingSession.create()
        session.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

