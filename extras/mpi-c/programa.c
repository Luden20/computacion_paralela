#include <stdio.h>
#include <mpi.h>
#include <string.h>

int main(int argc,char *argv[]){

	int rank,procesos;
	char data[100];
	int len=0;
	MPI_Init(&argc,&argv);

	MPI_Comm_rank(MPI_COMM_WORLD,&rank);
	MPI_Comm_size(MPI_COMM_WORLD,&procesos);

	printf("Hola desde el proceso %d de %d \n",rank,procesos);

	if(rank==0){
		strcpy(data,"Mensaje desde el root");
		len=strlen(data)+1;
	}

	MPI_Bcast(&data,len,MPI_INT,0,MPI_COMM_WORLD);
	printf("El dato que llego por bdcast al proceso %d fue %s \n",rank,data);

	MPI_Finalize();
	return 0;
}
